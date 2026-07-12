"""
Kiro AI Platform - License Manager

This module provides license management for commercial features.
"""
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from .settings import get_settings
from .features import FeatureFlags

logger = logging.getLogger(__name__)


class LicenseManager:
    """License Manager"""
    
    def __init__(self, license_file: Optional[str] = None):
        """
        Initialize license manager
        
        Args:
            license_file: Path to license file (optional)
        """
        settings = get_settings()
        self.license_file = license_file or settings.LICENSE_FILE
        self._license_data: Optional[Dict] = None
    
    def load_license(self) -> Dict:
        """
        Load license from file
        
        Returns:
            License data dictionary
        """
        if self._license_data is not None:
            return self._license_data
        
        if not os.path.exists(self.license_file):
            logger.info(f"License file {self.license_file} not found")
            self._license_data = {"status": "unlicensed"}
            return self._license_data
        
        try:
            with open(self.license_file, "r") as f:
                self._license_data = json.load(f)
                logger.info(f"Loaded license: {self._license_data.get('license_type', 'unknown')}")
                return self._license_data
        except Exception as e:
            logger.error(f"Failed to load license file: {e}")
            self._license_data = {"status": "invalid", "error": str(e)}
            return self._license_data
    
    def is_license_valid(self) -> bool:
        """
        Check if license is valid
        
        Returns:
            True if valid, False otherwise
        """
        license_data = self.load_license()
        
        # Check status
        if license_data.get("status") != "active":
            return False
        
        # Check expiry date
        expiry = license_data.get("expiry_date")
        if expiry:
            try:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                if expiry_date < datetime.now():
                    logger.warning(f"License expired on {expiry}")
                    return False
            except ValueError:
                logger.error(f"Invalid expiry date format: {expiry}")
                return False
        
        # Check for required fields
        required_fields = ["license_type", "customer"]
        for field in required_fields:
            if field not in license_data:
                logger.error(f"Missing required field in license: {field}")
                return False
        
        return True
    
    def get_license_type(self) -> str:
        """
        Get license type
        
        Returns:
            License type (e.g., 'basic', 'professional', 'enterprise')
        """
        license_data = self.load_license()
        return license_data.get("license_type", "unlicensed")
    
    def get_customer_name(self) -> str:
        """
        Get customer name from license
        
        Returns:
            Customer name
        """
        license_data = self.load_license()
        return license_data.get("customer", "Unknown")
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of enabled features from license
        
        Returns:
            List of feature names
        """
        license_data = self.load_license()
        return license_data.get("features", [])
    
    def apply_license_features(self) -> None:
        """
        Apply license features to system settings
        """
        if not self.is_license_valid():
            logger.info("No valid license, using default settings")
            return
        
        features = self.get_enabled_features()
        
        # Map features to settings
        feature_settings = {
            "multi_tenant": "MULTI_TENANT_ENABLED",
            "cross_org_sharing": "CROSS_ORG_SHARING_ENABLED",
            "audit_logging": "AUDIT_LOGGING_ENABLED",
            "sso": "SSO_ENABLED",
        }
        
        settings = get_settings()
        
        # Enable features from license
        for feature in features:
            setting_name = feature_settings.get(feature)
            if setting_name:
                setattr(settings, setting_name, True)
                logger.info(f"Enabled feature from license: {feature}")
        
        # Check for special 'all' feature
        if "all" in features:
            for setting_name in feature_settings.values():
                setattr(settings, setting_name, True)
            logger.info("Enabled all commercial features from license")
    
    def is_feature_included(self, feature: str) -> bool:
        """
        Check if a feature is included in the license
        
        Args:
            feature: Feature name
            
        Returns:
            True if included, False otherwise
        """
        features = self.get_enabled_features()
        return feature in features or "all" in features
    
    def get_remaining_days(self) -> Optional[int]:
        """
        Get remaining days until license expiry
        
        Returns:
            Number of days remaining, or None if no expiry
        """
        license_data = self.load_license()
        expiry = license_data.get("expiry_date")
        
        if not expiry:
            return None
        
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            remaining = (expiry_date - datetime.now()).days
            return max(0, remaining)
        except ValueError:
            return None
    
    def reload(self) -> None:
        """Reload license from file"""
        self._license_data = None
        self.load_license()
        
        # Re-apply features
        settings = get_settings()
        
        # Reset all features
        settings.MULTI_TENANT_ENABLED = False
        settings.CROSS_ORG_SHARING_ENABLED = False
        settings.AUDIT_LOGGING_ENABLED = False
        settings.SSO_ENABLED = False
        
        # Re-apply from license
        self.apply_license_features()


# Global license manager instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get global license manager instance"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
