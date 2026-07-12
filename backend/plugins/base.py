"""
Kiro AI Platform - Plugin System Base

This module provides the base class for all plugins.
"""
from abc import ABC, abstractmethod
from typing import List, Type, Any
from fastapi import FastAPI


class PluginBase(ABC):
    """Plugin base class"""
    
    name: str = ""
    version: str = "1.1.0"
    description: str = ""
    
    @abstractmethod
    def register(self, app: FastAPI) -> None:
        """
        Register plugin routes and components
        
        Args:
            app: FastAPI application instance
        """
        pass
    
    def get_models(self) -> List[Type]:
        """
        Return plugin data models
        
        Returns:
            List of model classes
        """
        return []
    
    def get_services(self) -> List[Any]:
        """
        Return plugin services
        
        Returns:
            List of service instances
        """
        return []
    
    def get_middleware(self):
        """
        Return plugin middleware
        
        Returns:
            List of middleware functions
        """
        return []
    
    def migrate(self) -> None:
        """
        Execute database migrations
        """
        pass
    
    def get_depends(self) -> List[str]:
        """
        Return list of plugin names this plugin depends on
        
        Returns:
            List of plugin names
        """
        return []
    
    def is_enabled(self) -> bool:
        """
        Check if plugin is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return True
    
    def __repr__(self) -> str:
        return f"<Plugin: {self.name} v{self.version}>"
