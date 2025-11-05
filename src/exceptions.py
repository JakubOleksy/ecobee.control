"""
Custom exceptions for Ecobee Automation
"""


class EcobeeAutomationError(Exception):
    """Base exception for ecobee automation errors."""
    pass


class LoginError(EcobeeAutomationError):
    """Exception raised when login fails."""
    pass


class NavigationError(EcobeeAutomationError):
    """Exception raised when navigation fails."""
    pass


class ElementNotFoundError(EcobeeAutomationError):
    """Exception raised when required web elements are not found."""
    pass


class ConfigurationError(EcobeeAutomationError):
    """Exception raised when configuration is invalid or missing."""
    pass


class TemperatureError(EcobeeAutomationError):
    """Exception raised when temperature operations fail."""
    pass


class ModeError(EcobeeAutomationError):
    """Exception raised when mode changes fail."""
    pass