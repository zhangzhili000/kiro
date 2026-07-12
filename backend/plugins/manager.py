"""
Kiro AI Platform - Plugin Manager

This module provides the plugin manager for loading and managing plugins.
"""
import importlib
import os
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI

from .base import PluginBase

logger = logging.getLogger(__name__)


class PluginManager:
    """Plugin Manager"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.loaded_plugins: List[str] = []
    
    def register_plugin(self, plugin: PluginBase) -> None:
        """
        Register a plugin
        
        Args:
            plugin: Plugin instance
        """
        if not plugin.name:
            raise ValueError("Plugin must have a name")
        
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} already registered, skipping")
            return
        
        # Check dependencies
        for dep in plugin.get_depends():
            if dep not in self.plugins:
                logger.error(f"Plugin {plugin.name} depends on {dep}, which is not loaded")
                raise RuntimeError(f"Missing dependency: {dep}")
        
        self.plugins[plugin.name] = plugin
        self.loaded_plugins.append(plugin.name)
        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """
        Unregister a plugin
        
        Args:
            plugin_name: Name of plugin to unregister
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} not found")
            return
        
        # Check if any plugin depends on this plugin
        for name, plugin in self.plugins.items():
            if plugin_name in plugin.get_depends():
                logger.error(f"Cannot unload {plugin_name}: {name} depends on it")
                raise RuntimeError(f"Plugin {plugin_name} is required by {name}")
        
        del self.plugins[plugin_name]
        self.loaded_plugins.remove(plugin_name)
        logger.info(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        Get a plugin by name
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> List[PluginBase]:
        """
        Get all registered plugins
        
        Returns:
            List of all plugins
        """
        return list(self.plugins.values())
    
    def load_plugins_from_dir(self, plugin_dir: str) -> None:
        """
        Load all plugins from a directory
        
        Args:
            plugin_dir: Directory containing plugins
        """
        if not os.path.exists(plugin_dir):
            logger.info(f"Plugin directory {plugin_dir} does not exist, skipping")
            return
        
        if not os.path.isdir(plugin_dir):
            logger.error(f"{plugin_dir} is not a directory")
            return
        
        # Scan directory for plugins
        for module_name in os.listdir(plugin_dir):
            if module_name.startswith("_") or module_name.startswith("."):
                continue
            
            module_path = os.path.join(plugin_dir, module_name)
            if not os.path.isdir(module_path):
                continue
            
            # Try to load plugin.py
            plugin_file = os.path.join(module_path, "plugin.py")
            if not os.path.exists(plugin_file):
                continue
            
            try:
                # Dynamic import
                spec = importlib.util.spec_from_file_location(
                    f"{module_name}.plugin",
                    plugin_file
                )
                
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for 'plugin' attribute
                    if hasattr(module, "plugin"):
                        plugin_instance = module.plugin
                        if isinstance(plugin_instance, PluginBase):
                            self.register_plugin(plugin_instance)
                        else:
                            logger.error(f"Plugin in {plugin_file} is not a PluginBase instance")
                    else:
                        logger.warning(f"No 'plugin' attribute found in {plugin_file}")
                        
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")
                import traceback
                traceback.print_exc()
    
    def register_all(self, app: FastAPI) -> None:
        """
        Register all plugins with the FastAPI app
        
        Args:
            app: FastAPI application instance
        """
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    plugin.register(app)
                except Exception as e:
                    logger.error(f"Failed to register plugin {plugin.name}: {e}")
                    import traceback
                    traceback.print_exc()
    
    def migrate_all(self) -> None:
        """Execute migrations for all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    plugin.migrate()
                except Exception as e:
                    logger.error(f"Failed to migrate plugin {plugin.name}: {e}")
                    import traceback
                    traceback.print_exc()


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
