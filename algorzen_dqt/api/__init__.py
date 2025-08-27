"""
API module for the Algorzen Data Quality Toolkit.

This module provides REST API endpoints for the React frontend.
"""

from .server import app as api_server

__all__ = ["api_server"]
