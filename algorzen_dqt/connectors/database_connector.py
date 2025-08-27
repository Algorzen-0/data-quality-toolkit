"""
Database Connectors for the Algorzen Data Quality Toolkit.

This module provides database connectors for various database systems:
- PostgreSQL
- MySQL
- MongoDB
- SQLite
- Oracle (placeholder)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import mysql.connector
from mysql.connector import Error as MySQLError
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import Error as PostgreSQLError

from .base import DataConnector, ConnectionConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseConfig(ConnectionConfig):
    """Configuration for database connections."""
    
    # Connection parameters
    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: str
    
    # Connection pool settings
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # SSL settings
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    
    # Timeout settings
    connect_timeout: int = 10
    read_timeout: int = 30
    write_timeout: int = 30
    
    # Additional parameters
    charset: str = "utf8"
    autocommit: bool = False
    isolation_level: Optional[str] = None


class PostgreSQLConnector(DataConnector):
    """PostgreSQL database connector."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize PostgreSQL connector."""
        super().__init__(config)
        self.engine: Optional[Engine] = None
        self.connection = None
        self._connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        params = {
            'host': self.config.host,
            'port': self.config.port,
            'database': self.config.database,
            'user': self.config.username,
            'password': self.config.password,
            'sslmode': self.config.ssl_mode,
            'connect_timeout': self.config.connect_timeout,
            'options': f'-c statement_timeout={self.config.read_timeout * 1000}'
        }
        
        # Add SSL parameters if specified
        if self.config.ssl_cert:
            params['sslcert'] = self.config.ssl_cert
        if self.config.ssl_key:
            params['sslkey'] = self.config.ssl_key
        if self.config.ssl_ca:
            params['sslrootcert'] = self.config.ssl_ca
        
        # Build connection string
        conn_str = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
        
        return conn_str
    
    async def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            # Create SQLAlchemy engine with connection pooling
            self.engine = create_engine(
                self._connection_string,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Connected to PostgreSQL database: {self.config.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from PostgreSQL database."""
        try:
            if self.engine:
                self.engine.dispose()
                self.engine = None
            
            if self.connection:
                self.connection.close()
                self.connection = None
            
            logger.info("Disconnected from PostgreSQL database")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from PostgreSQL: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"PostgreSQL version: {version}")
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            schema_info = {
                "tables": [],
                "views": [],
                "functions": [],
                "total_size": 0
            }
            
            with self.engine.connect() as conn:
                # Get tables
                tables_query = """
                SELECT 
                    schemaname, tablename, tableowner, 
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename
                """
                
                result = conn.execute(text(tables_query))
                for row in result:
                    schema_info["tables"].append({
                        "schema": row[0],
                        "table": row[1],
                        "owner": row[2],
                        "size": row[3]
                    })
                
                # Get views
                views_query = """
                SELECT schemaname, viewname, viewowner
                FROM pg_views 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                """
                
                result = conn.execute(text(views_query))
                for row in result:
                    schema_info["views"].append({
                        "schema": row[0],
                        "view": row[1],
                        "owner": row[2]
                    })
                
                # Get database size
                size_query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
                result = conn.execute(text(size_query))
                schema_info["total_size"] = result.fetchone()[0]
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {}
    
    async def load_data(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None
    ) -> pd.DataFrame:
        """Load data from PostgreSQL using SQL query."""
        try:
            if chunk_size:
                # Load data in chunks for large datasets
                chunks = []
                offset = 0
                
                while True:
                    chunk_query = f"{query} LIMIT {chunk_size} OFFSET {offset}"
                    chunk_df = pd.read_sql(chunk_query, self.engine, params=params)
                    
                    if chunk_df.empty:
                        break
                    
                    chunks.append(chunk_df)
                    offset += chunk_size
                    
                    if len(chunk_df) < chunk_size:
                        break
                
                if chunks:
                    return pd.concat(chunks, ignore_index=True)
                else:
                    return pd.DataFrame()
            else:
                # Load all data at once
                return pd.read_sql(query, self.engine, params=params)
                
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Execute a non-SELECT query."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(query), params or {})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return False
    
    async def get_table_info(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get detailed information about a specific table."""
        try:
            table_info = {
                "columns": [],
                "indexes": [],
                "constraints": [],
                "row_count": 0,
                "size": ""
            }
            
            with self.engine.connect() as conn:
                # Get column information
                columns_query = """
                SELECT 
                    column_name, data_type, is_nullable, column_default,
                    character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
                """
                
                result = conn.execute(text(columns_query), {"schema": schema, "table": table_name})
                for row in result:
                    table_info["columns"].append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3],
                        "max_length": row[4],
                        "precision": row[5],
                        "scale": row[6]
                    })
                
                # Get row count
                count_query = f"SELECT COUNT(*) FROM {schema}.{table_name}"
                result = conn.execute(text(count_query))
                table_info["row_count"] = result.fetchone()[0]
                
                # Get table size
                size_query = f"""
                SELECT pg_size_pretty(pg_total_relation_size('{schema}.{table_name}'))
                """
                result = conn.execute(text(size_query))
                table_info["size"] = result.fetchone()[0]
            
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}


class MySQLConnector(DataConnector):
    """MySQL database connector."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize MySQL connector."""
        super().__init__(config)
        self.connection = None
        self._connection_params = self._build_connection_params()
    
    def _build_connection_params(self) -> Dict[str, Any]:
        """Build MySQL connection parameters."""
        return {
            'host': self.config.host,
            'port': self.config.port,
            'database': self.config.database,
            'user': self.config.username,
            'password': self.config.password,
            'charset': self.config.charset,
            'autocommit': self.config.autocommit,
            'connect_timeout': self.config.connect_timeout,
            'read_timeout': self.config.read_timeout,
            'write_timeout': self.config.write_timeout,
            'ssl_disabled': self.config.ssl_mode == "disable"
        }
    
    async def connect(self) -> bool:
        """Connect to MySQL database."""
        try:
            self.connection = mysql.connector.connect(**self._connection_params)
            
            # Test connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            
            logger.info(f"Connected to MySQL database: {self.config.database} (Version: {version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MySQL database."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            
            logger.info("Disconnected from MySQL database")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from MySQL: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def load_data(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None
    ) -> pd.DataFrame:
        """Load data from MySQL using SQL query."""
        try:
            if chunk_size:
                # Load data in chunks
                chunks = []
                offset = 0
                
                while True:
                    chunk_query = f"{query} LIMIT {chunk_size} OFFSET {offset}"
                    chunk_df = pd.read_sql(chunk_query, self.connection, params=params)
                    
                    if chunk_df.empty:
                        break
                    
                    chunks.append(chunk_df)
                    offset += chunk_size
                    
                    if len(chunk_df) < chunk_size:
                        break
                
                if chunks:
                    return pd.concat(chunks, ignore_index=True)
                else:
                    return pd.DataFrame()
            else:
                # Load all data at once
                return pd.read_sql(query, self.connection, params=params)
                
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()


class MongoDBConnector(DataConnector):
    """MongoDB database connector."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize MongoDB connector."""
        super().__init__(config)
        self.client: Optional[MongoClient] = None
        self.database = None
        self._connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build MongoDB connection string."""
        auth_part = f"{self.config.username}:{self.config.password}@" if self.config.username else ""
        ssl_part = "?ssl=true" if self.config.ssl_mode != "disable" else ""
        
        return f"mongodb://{auth_part}{self.config.host}:{self.config.port}/{self.config.database}{ssl_part}"
    
    async def connect(self) -> bool:
        """Connect to MongoDB database."""
        try:
            self.client = MongoClient(
                self._connection_string,
                serverSelectionTimeoutMS=self.config.connect_timeout * 1000,
                socketTimeoutMS=self.config.read_timeout * 1000,
                connectTimeoutMS=self.config.connect_timeout * 1000
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.database = self.client[self.config.database]
            
            logger.info(f"Connected to MongoDB database: {self.config.database}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MongoDB database."""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.database = None
            
            logger.info("Disconnected from MongoDB database")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from MongoDB: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_schema(self) -> Dict[str, Any]:
        """Get MongoDB database schema information."""
        try:
            schema_info = {
                "collections": [],
                "total_size": 0
            }
            
            # Get collection information
            for collection_name in self.database.list_collection_names():
                collection = self.database[collection_name]
                stats = self.database.command("collStats", collection_name)
                
                schema_info["collections"].append({
                    "name": collection_name,
                    "count": stats.get("count", 0),
                    "size": stats.get("size", 0),
                    "avg_obj_size": stats.get("avgObjSize", 0),
                    "storage_size": stats.get("storageSize", 0),
                    "indexes": stats.get("nindexes", 0)
                })
            
            # Get database stats
            db_stats = self.database.command("dbStats")
            schema_info["total_size"] = db_stats.get("dataSize", 0)
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {}
    
    async def load_data(
        self, 
        collection_name: str,
        query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Load data from MongoDB collection."""
        try:
            collection = self.database[collection_name]
            
            # Build query
            mongo_query = query or {}
            mongo_projection = projection or {}
            
            # Execute query
            cursor = collection.find(mongo_query, mongo_projection)
            
            if limit:
                cursor = cursor.limit(limit)
            
            # Convert to DataFrame
            documents = list(cursor)
            if documents:
                return pd.DataFrame(documents)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pd.DataFrame()
    
    async def execute_query(self, query: Dict[str, Any], collection_name: str) -> bool:
        """Execute a MongoDB query (insert, update, delete)."""
        try:
            collection = self.database[collection_name]
            
            operation = query.get("operation")
            if operation == "insert":
                collection.insert_many(query.get("documents", []))
            elif operation == "update":
                collection.update_many(query.get("filter", {}), query.get("update", {}))
            elif operation == "delete":
                collection.delete_many(query.get("filter", {}))
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            return False


class DatabaseConnectorFactory:
    """Factory for creating database connectors."""
    
    @staticmethod
    def create_connector(db_type: str, config: DatabaseConfig) -> DataConnector:
        """Create a database connector based on type."""
        if db_type.lower() in ["postgresql", "postgres", "psql"]:
            return PostgreSQLConnector(config)
        elif db_type.lower() in ["mysql", "mariadb"]:
            return MySQLConnector(config)
        elif db_type.lower() in ["mongodb", "mongo"]:
            return MongoDBConnector(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
