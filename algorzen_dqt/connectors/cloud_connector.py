"""
Cloud Storage Connectors for the Algorzen Data Quality Toolkit.

This module provides cloud storage connectors for:
- AWS S3
- Azure Blob Storage
- Google Cloud Storage
- Local file system (fallback)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, BinaryIO
from datetime import datetime
import pandas as pd
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import azure.storage.blob
from azure.storage.blob import BlobServiceClient
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient
from azure.core.exceptions import AzureError
from google.cloud import storage
from google.cloud.storage import Client as GCSClient
from google.cloud.exceptions import GoogleCloudError
import os
from pathlib import Path
import tempfile
import json

from .base import DataConnector, ConnectionConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CloudStorageConfig(ConnectionConfig):
    """Configuration for cloud storage connections."""
    
    # Common settings
    storage_type: str  # "s3", "azure", "gcs", "local"
    bucket_name: str
    region: Optional[str] = None
    
    # AWS S3 settings
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    endpoint_url: Optional[str] = None  # For S3-compatible services
    
    # Azure settings
    connection_string: Optional[str] = None
    account_name: Optional[str] = None
    account_key: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # Google Cloud settings
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    credentials_json: Optional[str] = None
    
    # Security settings
    use_ssl: bool = True
    verify_ssl: bool = True
    
    # Performance settings
    max_concurrent_requests: int = 10
    chunk_size: int = 8192  # 8KB chunks for uploads/downloads


class S3Connector(DataConnector):
    """AWS S3 storage connector."""
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize S3 connector."""
        super().__init__(config)
        self.s3_client = None
        self.s3_resource = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup S3 client with credentials."""
        try:
            # Use environment variables if credentials not provided
            if not self.config.aws_access_key_id:
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.config.region,
                    endpoint_url=self.config.endpoint_url,
                    use_ssl=self.config.use_ssl,
                    verify=self.config.verify_ssl
                )
                self.s3_resource = boto3.resource(
                    's3',
                    region_name=self.config.region,
                    endpoint_url=self.config.endpoint_url,
                    use_ssl=self.config.use_ssl,
                    verify=self.config.verify_ssl
                )
            else:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.config.aws_access_key_id,
                    aws_secret_access_key=self.config.aws_secret_access_key,
                    aws_session_token=self.config.aws_session_token,
                    region_name=self.config.region,
                    endpoint_url=self.config.endpoint_url,
                    use_ssl=self.config.use_ssl,
                    verify=self.config.verify_ssl
                )
                self.s3_resource = boto3.resource(
                    's3',
                    aws_access_key_id=self.config.aws_access_key_id,
                    aws_secret_access_key=self.config.aws_secret_access_key,
                    aws_session_token=self.config.aws_session_token,
                    region_name=self.config.region,
                    endpoint_url=self.config.endpoint_url,
                    use_ssl=self.config.use_ssl,
                    verify=self.config.verify_ssl
                )
            
            logger.info(f"S3 client configured for bucket: {self.config.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup S3 client: {e}")
    
    async def connect(self) -> bool:
        """Connect to S3 bucket."""
        try:
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            logger.info(f"Connected to S3 bucket: {self.config.bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket not found: {self.config.bucket_name}")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket: {self.config.bucket_name}")
            else:
                logger.error(f"S3 connection error: {e}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except Exception as e:
            logger.error(f"Unexpected S3 error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from S3."""
        try:
            # S3 client doesn't need explicit disconnection
            logger.info("Disconnected from S3")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from S3: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test S3 connection."""
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            return True
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get S3 bucket schema (list of objects)."""
        try:
            schema_info = {
                "objects": [],
                "total_size": 0,
                "total_objects": 0,
                "prefixes": []
            }
            
            # List objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.config.bucket_name)
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        schema_info["objects"].append({
                            "key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "storage_class": obj.get('StorageClass', 'STANDARD')
                        })
                        schema_info["total_size"] += obj['Size']
                        schema_info["total_objects"] += 1
                
                if 'CommonPrefixes' in page:
                    for prefix in page['CommonPrefixes']:
                        schema_info["prefixes"].append(prefix['Prefix'])
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get S3 schema: {e}")
            return {}
    
    async def load_data(
        self, 
        object_key: str,
        file_format: str = "auto",
        chunk_size: Optional[int] = None
    ) -> pd.DataFrame:
        """Load data from S3 object."""
        try:
            # Download object to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                self.s3_client.download_file(
                    self.config.bucket_name, 
                    object_key, 
                    tmp_file.name
                )
                tmp_path = tmp_file.name
            
            try:
                # Load data based on file format
                if file_format == "auto":
                    file_format = self._detect_file_format(object_key)
                
                if file_format == "csv":
                    data = pd.read_csv(tmp_path)
                elif file_format == "json":
                    data = pd.read_json(tmp_path)
                elif file_format == "parquet":
                    data = pd.read_parquet(tmp_path)
                elif file_format == "excel":
                    data = pd.read_excel(tmp_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                return data
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Failed to load data from S3: {e}")
            return pd.DataFrame()
    
    async def upload_data(
        self, 
        data: pd.DataFrame, 
        object_key: str, 
        file_format: str = "csv"
    ) -> bool:
        """Upload data to S3."""
        try:
            # Save data to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                if file_format == "csv":
                    data.to_csv(tmp_file.name, index=False)
                elif file_format == "json":
                    data.to_json(tmp_file.name, orient="records")
                elif file_format == "parquet":
                    data.to_parquet(tmp_file.name, index=False)
                else:
                    raise ValueError(f"Unsupported upload format: {file_format}")
                
                tmp_path = tmp_file.name
            
            try:
                # Upload to S3
                self.s3_client.upload_file(
                    tmp_path, 
                    self.config.bucket_name, 
                    object_key
                )
                
                logger.info(f"Data uploaded to S3: s3://{self.config.bucket_name}/{object_key}")
                return True
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Failed to upload data to S3: {e}")
            return False
    
    def _detect_file_format(self, object_key: str) -> str:
        """Detect file format from object key."""
        extension = Path(object_key).suffix.lower()
        
        if extension == ".csv":
            return "csv"
        elif extension == ".json":
            return "json"
        elif extension in [".parquet", ".pq"]:
            return "parquet"
        elif extension in [".xlsx", ".xls"]:
            return "excel"
        else:
            return "csv"  # Default to CSV


class AzureBlobConnector(DataConnector):
    """Azure Blob Storage connector."""
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize Azure Blob connector."""
        super().__init__(config)
        self.blob_service_client = None
        self.container_client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Azure Blob client."""
        try:
            if self.config.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.config.connection_string
                )
            elif self.config.account_name and self.config.account_key:
                account_url = f"https://{self.config.account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.config.account_key
                )
            else:
                # Use default credentials from environment
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
                )
            
            self.container_client = self.blob_service_client.get_container_client(
                self.config.bucket_name
            )
            
            logger.info(f"Azure Blob client configured for container: {self.config.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup Azure Blob client: {e}")
    
    async def connect(self) -> bool:
        """Connect to Azure Blob container."""
        try:
            # Test container access
            properties = self.container_client.get_container_properties()
            logger.info(f"Connected to Azure Blob container: {self.config.bucket_name}")
            return True
            
        except AzureError as e:
            logger.error(f"Azure Blob connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected Azure Blob error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Azure Blob."""
        try:
            # Azure client doesn't need explicit disconnection
            logger.info("Disconnected from Azure Blob")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Azure Blob: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Azure Blob connection."""
        try:
            self.container_client.get_container_properties()
            return True
        except Exception as e:
            logger.error(f"Azure Blob connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get Azure Blob container schema (list of blobs)."""
        try:
            schema_info = {
                "blobs": [],
                "total_size": 0,
                "total_blobs": 0
            }
            
            # List blobs in container
            blobs = self.container_client.list_blobs()
            
            for blob in blobs:
                schema_info["blobs"].append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified.isoformat(),
                    "blob_type": blob.blob_type
                })
                schema_info["total_size"] += blob.size
                schema_info["total_blobs"] += 1
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get Azure Blob schema: {e}")
            return {}
    
    async def load_data(
        self, 
        blob_name: str,
        file_format: str = "auto"
    ) -> pd.DataFrame:
        """Load data from Azure Blob."""
        try:
            # Download blob to temporary file
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                with open(tmp_file.name, "wb") as f:
                    blob_data = blob_client.download_blob()
                    f.write(blob_data.readall())
                
                tmp_path = tmp_file.name
            
            try:
                # Load data based on file format
                if file_format == "auto":
                    file_format = self._detect_file_format(blob_name)
                
                if file_format == "csv":
                    data = pd.read_csv(tmp_path)
                elif file_format == "json":
                    data = pd.read_json(tmp_path)
                elif file_format == "parquet":
                    data = pd.read_parquet(tmp_path)
                elif file_format == "excel":
                    data = pd.read_excel(tmp_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                return data
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Failed to load data from Azure Blob: {e}")
            return pd.DataFrame()
    
    def _detect_file_format(self, blob_name: str) -> str:
        """Detect file format from blob name."""
        extension = Path(blob_name).suffix.lower()
        
        if extension == ".csv":
            return "csv"
        elif extension == ".json":
            return "json"
        elif extension in [".parquet", ".pq"]:
            return "parquet"
        elif extension in [".xlsx", ".xls"]:
            return "excel"
        else:
            return "csv"  # Default to CSV


class GCSConnector(DataConnector):
    """Google Cloud Storage connector."""
    
    def __init__(self, config: CloudStorageConfig):
        """Initialize GCS connector."""
        super().__init__(config)
        self.gcs_client = None
        self.bucket = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup GCS client."""
        try:
            if self.config.credentials_path:
                # Use service account key file
                self.gcs_client = GCSClient.from_service_account_json(
                    self.config.credentials_path,
                    project=self.config.project_id
                )
            elif self.config.credentials_json:
                # Use service account JSON string
                import json
                credentials_info = json.loads(self.config.credentials_json)
                self.gcs_client = GCSClient.from_service_account_info(
                    credentials_info,
                    project=self.config.project_id
                )
            else:
                # Use default credentials from environment
                self.gcs_client = GCSClient(project=self.config.project_id)
            
            self.bucket = self.gcs_client.bucket(self.config.bucket_name)
            
            logger.info(f"GCS client configured for bucket: {self.config.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup GCS client: {e}")
    
    async def connect(self) -> bool:
        """Connect to GCS bucket."""
        try:
            # Test bucket access
            self.bucket.reload()
            logger.info(f"Connected to GCS bucket: {self.config.bucket_name}")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"GCS connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected GCS error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from GCS."""
        try:
            # GCS client doesn't need explicit disconnection
            logger.info("Disconnected from GCS")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from GCS: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test GCS connection."""
        try:
            self.bucket.reload()
            return True
        except Exception as e:
            logger.error(f"GCS connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get GCS bucket schema (list of blobs)."""
        try:
            schema_info = {
                "blobs": [],
                "total_size": 0,
                "total_blobs": 0
            }
            
            # List blobs in bucket
            blobs = self.gcs_client.list_blobs(self.config.bucket_name)
            
            for blob in blobs:
                schema_info["blobs"].append({
                    "name": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat(),
                    "storage_class": blob.storage_class
                })
                schema_info["total_size"] += blob.size
                schema_info["total_blobs"] += 1
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get GCS schema: {e}")
            return {}
    
    async def load_data(
        self, 
        blob_name: str,
        file_format: str = "auto"
    ) -> pd.DataFrame:
        """Load data from GCS blob."""
        try:
            # Download blob to temporary file
            blob = self.bucket.blob(blob_name)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                blob.download_to_filename(tmp_file.name)
                tmp_path = tmp_file.name
            
            try:
                # Load data based on file format
                if file_format == "auto":
                    file_format = self._detect_file_format(blob_name)
                
                if file_format == "csv":
                    data = pd.read_csv(tmp_path)
                elif file_format == "json":
                    data = pd.read_json(tmp_path)
                elif file_format == "parquet":
                    data = pd.read_parquet(tmp_path)
                elif file_format == "excel":
                    data = pd.read_excel(tmp_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                
                return data
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Failed to load data from GCS: {e}")
            return pd.DataFrame()
    
    def _detect_file_format(self, blob_name: str) -> str:
        """Detect file format from blob name."""
        extension = Path(blob_name).suffix.lower()
        
        if extension == ".csv":
            return "csv"
        elif extension == ".json":
            return "json"
        elif extension in [".parquet", ".pq"]:
            return "parquet"
        elif extension in [".xlsx", ".xls"]:
            return "excel"
        else:
            return "csv"  # Default to CSV


class CloudStorageConnectorFactory:
    """Factory for creating cloud storage connectors."""
    
    @staticmethod
    def create_connector(storage_type: str, config: CloudStorageConfig) -> DataConnector:
        """Create a cloud storage connector based on type."""
        if storage_type.lower() in ["s3", "aws"]:
            return S3Connector(config)
        elif storage_type.lower() in ["azure", "blob"]:
            return AzureBlobConnector(config)
        elif storage_type.lower() in ["gcs", "google", "gcp"]:
            return GCSConnector(config)
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
