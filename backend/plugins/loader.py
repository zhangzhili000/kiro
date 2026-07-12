"""
Kiro AI Platform - Plugin Loader

This module provides the plugin loader that integrates with the license system.
"""
import logging
import os
from typing import Optional
from fastapi import FastAPI

from .manager import get_plugin_manager, PluginManager
from ..core.license_manager import get_license_manager

logger = logging.getLogger(__name__)


def load_commercial_plugins(
    app: FastAPI,
    plugin_dir: str = "commercial",
    license_manager=None
) -> Optional[PluginManager]:
    """
    Load commercial plugins based on license
    
    Args:
        app: FastAPI application instance
        plugin_dir: Directory containing commercial plugins
        license_manager: License manager instance (optional)
        
    Returns:
        PluginManager instance or None
    """
    # Get license manager
    if license_manager is None:
        license_manager = get_license_manager()
    
    # Check license validity
    if not license_manager.is_license_valid():
        logger.info("No valid license found, skipping commercial plugins")
        return None
    
    # Apply license features
    license_manager.apply_license_features()
    
    # Get enabled features
    enabled_features = license_manager.get_enabled_features()
    logger.info(f"Enabled features: {enabled_features}")
    
    # Get plugin manager
    manager = get_plugin_manager()
    
    # Load plugins from directory
    if os.path.exists(plugin_dir) and os.path.isdir(plugin_dir):
        manager.load_plugins_from_dir(plugin_dir)
        
        # Filter plugins based on enabled features
        for plugin in manager.get_all_plugins():
            plugin_name = plugin.name.replace("kiro-", "")
            
            # Check if this feature is enabled
            if plugin_name not in enabled_features and "all" not in enabled_features:
                logger.info(f"Plugin {plugin.name} is not enabled in license, skipping")
                # Note: We don't unregister it, just mark as disabled
                # The plugin itself will check is_enabled()
    
    # Register all enabled plugins
    manager.register_all(app)
    
    logger.info(f"Loaded {len(manager.get_all_plugins())} commercial plugins")
    return manager


def load_plugin_by_name(
    app: FastAPI,
    plugin_name: str,
    plugin_dir: str = "commercial"
) -> bool:
    """
    Load a specific plugin by name
    
    Args:
        app: FastAPI application instance
        plugin_name: Name of plugin to load
        plugin_dir: Directory containing plugins
        
    Returns:
        True if loaded successfully, False otherwise
    """
    plugin_path = os.path.join(plugin_dir, plugin_name)
    
    if not os.path.exists(plugin_path):
        logger.error(f"Plugin directory {plugin_path} not found")
        return False
    
    manager = get_plugin_manager()
    manager.load_plugins_from_dir(plugin_dir)
    
    plugin = manager.get_plugin(plugin_name)
    if plugin and plugin.is_enabled():
        try:
            plugin.register(app)
            return True
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_name}: {e}")
            return False
    
    return False


__all__ = [
    "load_commercial_plugins",
    "load_plugin_by_name",
    "get_plugin_manager",
    "PluginManager"
]
