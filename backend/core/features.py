"""
Kiro AI Platform - Feature Flags

This module provides feature flags for controlling commercial features.
"""
from typing import List
from .settings import get_settings


class FeatureFlags:
    """Feature Flags"""
    
    @staticmethod
    def is_multi_tenant_enabled() -> bool:
        """
        Check if multi-tenant mode is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return get_settings().MULTI_TENANT_ENABLED
    
    @staticmethod
    def is_cross_org_sharing_enabled() -> bool:
        """
        Check if cross-organization sharing is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return get_settings().CROSS_ORG_SHARING_ENABLED
    
    @staticmethod
    def is_audit_logging_enabled() -> bool:
        """
        Check if audit logging is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return get_settings().AUDIT_LOGGING_ENABLED
    
    @staticmethod
    def is_sso_enabled() -> bool:
        """
        Check if SSO is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return get_settings().SSO_ENABLED
    
    @staticmethod
    def get_enabled_features() -> List[str]:
        """
        Get list of enabled features
        
        Returns:
            List of feature names
        """
        settings = get_settings()
        features = []
        
        if settings.MULTI_TENANT_ENABLED:
            features.append("multi_tenant")
        if settings.CROSS_ORG_SHARING_ENABLED:
            features.append("cross_org_sharing")
        if settings.AUDIT_LOGGING_ENABLED:
            features.append("audit_logging")
        if settings.SSO_ENABLED:
            features.append("sso")
        
        return features
    
    @staticmethod
    def is_feature_enabled(feature: str) -> bool:
        """
        Check if a specific feature is enabled
        
        Args:
            feature: Feature name
            
        Returns:
            True if enabled, False otherwise
        """
        settings = get_settings()
        
        feature_map = {
            "multi_tenant": settings.MULTI_TENANT_ENABLED,
            "cross_org_sharing": settings.CROSS_ORG_SHARING_ENABLED,
            "audit_logging": settings.AUDIT_LOGGING_ENABLED,
            "sso": settings.SSO_ENABLED,
        }
        
        return feature_map.get(feature, False)
    
    @staticmethod
    def enable_feature(feature: str) -> bool:
        """
        Enable a specific feature
        
        Args:
            feature: Feature name
            
        Returns:
            True if enabled, False if feature not found
        """
        settings = get_settings()
        
        feature_map = {
            "multi_tenant": "MULTI_TENANT_ENABLED",
            "cross_org_sharing": "CROSS_ORG_SHARING_ENABLED",
            "audit_logging": "AUDIT_LOGGING_ENABLED",
            "sso": "SSO_ENABLED",
        }
        
        setting_name = feature_map.get(feature)
        if setting_name:
            setattr(settings, setting_name, True)
            return True
        
        return False
    
    @staticmethod
    def disable_feature(feature: str) -> bool:
        """
        Disable a specific feature
        
        Args:
            feature: Feature name
            
        Returns:
            True if disabled, False if feature not found
        """
        settings = get_settings()
        
        feature_map = {
            "multi_tenant": "MULTI_TENANT_ENABLED",
            "cross_org_sharing": "CROSS_ORG_SHARING_ENABLED",
            "audit_logging": "AUDIT_LOGGING_ENABLED",
            "sso": "SSO_ENABLED",
        }
        
        setting_name = feature_map.get(feature)
        if setting_name:
            setattr(settings, setting_name, False)
            return True
        
        return False
