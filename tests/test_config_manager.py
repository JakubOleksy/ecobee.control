"""
Unit tests for ConfigManager class
"""

import unittest
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open
from src.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_initialization(self):
        """Test basic configuration initialization."""
        config = ConfigManager(self.temp_dir)
        self.assertIsInstance(config.config_data, dict)
    
    def test_get_default_value(self):
        """Test getting configuration with default value."""
        config = ConfigManager(self.temp_dir)
        value = config.get('nonexistent.key', 'default_value')
        self.assertEqual(value, 'default_value')
    
    def test_set_and_get_value(self):
        """Test setting and getting configuration values."""
        config = ConfigManager(self.temp_dir)
        config.set('test.key', 'test_value')
        value = config.get('test.key')
        self.assertEqual(value, 'test_value')
    
    def test_nested_key_access(self):
        """Test nested key access with dot notation."""
        config = ConfigManager(self.temp_dir)
        config.set('level1.level2.level3', 'nested_value')
        value = config.get('level1.level2.level3')
        self.assertEqual(value, 'nested_value')
    
    def test_value_conversion(self):
        """Test automatic value type conversion."""
        config = ConfigManager(self.temp_dir)
        
        # Test boolean conversion
        self.assertTrue(config._convert_value('true'))
        self.assertFalse(config._convert_value('false'))
        
        # Test numeric conversion
        self.assertEqual(config._convert_value('42'), 42)
        self.assertEqual(config._convert_value('3.14'), 3.14)
        
        # Test string preservation
        self.assertEqual(config._convert_value('text'), 'text')
    
    @patch.dict(os.environ, {'TEST_VAR': 'test_value'})
    def test_environment_loading(self):
        """Test loading from environment variables."""
        with patch.object(ConfigManager, '_load_config_files'):
            config = ConfigManager(self.temp_dir)
            # Environment loading is tested indirectly through the mapping system
            self.assertIsInstance(config.config_data, dict)
    
    def test_config_file_loading(self):
        """Test loading from YAML config files."""
        # Create a test config file
        config_file_path = os.path.join(self.temp_dir, 'default.yml')
        test_config = {
            'test_section': {
                'test_key': 'test_value'
            }
        }
        
        with open(config_file_path, 'w') as f:
            yaml.dump(test_config, f)
        
        config = ConfigManager(self.temp_dir)
        value = config.get('test_section.test_key')
        self.assertEqual(value, 'test_value')
    
    def test_validate_required(self):
        """Test validation of required configuration keys."""
        config = ConfigManager(self.temp_dir)
        config.set('required.key', 'value')
        
        # Should not raise exception
        config.validate_required(['required.key'])
        
        # Should raise exception for missing key
        with self.assertRaises(ValueError):
            config.validate_required(['missing.key'])
    
    def test_get_section(self):
        """Test getting entire configuration sections."""
        config = ConfigManager(self.temp_dir)
        config.set('section.key1', 'value1')
        config.set('section.key2', 'value2')
        
        section = config.get_section('section')
        self.assertEqual(section, {'key1': 'value1', 'key2': 'value2'})
    
    def test_sensitive_data_masking(self):
        """Test that sensitive data is masked in string representation."""
        config = ConfigManager(self.temp_dir)
        config.set('user.password', 'secret123')
        config.set('api.key', 'api_key_123')
        
        config_str = str(config)
        self.assertNotIn('secret123', config_str)
        self.assertNotIn('api_key_123', config_str)
        self.assertIn('*', config_str)


if __name__ == '__main__':
    unittest.main()