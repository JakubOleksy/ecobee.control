"""
Configuration Manager for Ecobee Automation

Handles loading configuration from environment variables, config files,
and provides a unified interface for accessing settings.
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv


class ConfigManager:
    """Manages configuration loading and access for the ecobee automation."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory containing config files. Defaults to ../config
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up paths
        if config_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(current_dir, '..', 'config')
        
        self.config_dir = config_dir
        self.config_data: Dict[str, Any] = {}
        
        # Load configuration
        self._load_environment()
        self._load_config_files()

    def _load_environment(self) -> None:
        """Load environment variables from .env file and system environment."""
        try:
            # Load from .env file if it exists
            env_file = os.path.join(os.path.dirname(self.config_dir), '.env')
            if os.path.exists(env_file):
                load_dotenv(env_file)
                self.logger.info(f"Loaded environment from: {env_file}")
            
            # Map environment variables to config keys
            env_mappings = {
                'ECOBEE_USERNAME': 'ecobee.username',
                'ECOBEE_PASSWORD': 'ecobee.password',
                'WEBDRIVER_HEADLESS': 'webdriver.headless',
                'WEBDRIVER_IMPLICIT_WAIT': 'webdriver.implicit_wait',
                'WEBDRIVER_PAGE_LOAD_TIMEOUT': 'webdriver.page_load_timeout',
                'AUTOMATION_DELAY': 'automation.delay',
                'MAX_RETRY_ATTEMPTS': 'automation.max_retry_attempts',
                'SCREENSHOT_ON_ERROR': 'automation.screenshot_on_error',
                'LOG_LEVEL': 'logging.level',
                'LOG_FILE': 'logging.file',
            }
            
            for env_var, config_key in env_mappings.items():
                value = os.getenv(env_var)
                if value is not None:
                    # Convert string values to appropriate types
                    converted_value = self._convert_value(value)
                    self._set_nested_key(self.config_data, config_key, converted_value)
            
        except Exception as e:
            self.logger.warning(f"Failed to load environment variables: {e}")

    def _load_config_files(self) -> None:
        """Load configuration from YAML files."""
        try:
            config_files = ['default.yml', 'config.yml', 'local.yml']
            
            for config_file in config_files:
                config_path = os.path.join(self.config_dir, config_file)
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        file_config = yaml.safe_load(f)
                        if file_config:
                            self._merge_config(self.config_data, file_config)
                            self.logger.info(f"Loaded config from: {config_path}")
                
        except Exception as e:
            self.logger.warning(f"Failed to load config files: {e}")

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate Python type."""
        if not isinstance(value, str):
            return value
        
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string if no conversion applies
        return value

    def _set_nested_key(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set a nested key in a dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value

    def _get_nested_key(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get a nested key from a dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'ecobee.username')
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self._get_nested_key(self.config_data, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation
            value: Value to set
        """
        self._set_nested_key(self.config_data, key, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary containing section configuration
        """
        return self.get(section, {})

    def validate_required(self, required_keys: list) -> None:
        """Validate that required configuration keys are present.
        
        Args:
            required_keys: List of required configuration keys
            
        Raises:
            ValueError: If any required key is missing
        """
        missing_keys = []
        
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration keys: {missing_keys}")

    def to_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary."""
        return self.config_data.copy()

    def __str__(self) -> str:
        """String representation of configuration (without sensitive data)."""
        safe_config = self.to_dict()
        
        # Mask sensitive keys
        sensitive_keys = ['password', 'key', 'secret', 'token']
        
        def mask_sensitive(data: Dict[str, Any]) -> Dict[str, Any]:
            masked = {}
            for k, v in data.items():
                if isinstance(v, dict):
                    masked[k] = mask_sensitive(v)
                elif any(sensitive in k.lower() for sensitive in sensitive_keys):
                    masked[k] = '*' * len(str(v)) if v else None
                else:
                    masked[k] = v
            return masked
        
        return str(mask_sensitive(safe_config))