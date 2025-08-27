"""
Base data connector class.

This module defines the base interface for all data connectors in the
Algorzen Data Quality Toolkit.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List
import pandas as pd
from pydantic import BaseModel

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ConnectionConfig(BaseModel):
    """Configuration for data source connections."""
    source_type: str
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    max_connections: int = 10
    ssl_mode: Optional[str] = None
    additional_params: Dict[str, Any] = {}


class DataConnector(ABC):
    """
    Abstract base class for data connectors.
    
    All data connectors must implement this interface to ensure
    consistent behavior across different data sources.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize the data connector.
        
        Args:
            config: Connection configuration
        """
        self.config = config
        self.is_connected = False
        self.connection = None
        self._lock = asyncio.Lock()
        
        logger.debug(f"Initialized {self.__class__.__name__} with config: {config.source_type}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the data source.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the data source."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if the connection is working.
        
        Returns:
            True if connection is working, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """
        Get the schema information for the data source.
        
        Returns:
            Dictionary containing schema information
        """
        pass
    
    @abstractmethod
    async def load_data(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load data from the source.
        
        Args:
            query: Optional query to execute
            filters: Optional filters to apply
            limit: Optional limit on number of rows
            
        Returns:
            Loaded data as pandas DataFrame
        """
        pass
    
    @abstractmethod
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the data source.
        
        Returns:
            Dictionary containing metadata information
        """
        pass
    
    async def close(self) -> None:
        """Close the connector and clean up resources."""
        await self.disconnect()
        logger.info(f"Closed {self.__class__.__name__}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        asyncio.create_task(self.close())
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
