# Ecobee Web Automation Project Instructions

This project automates the navigation of the ecobee web UI to control heating system status using Python and Selenium.

## Project Context
- **Purpose**: Automate ecobee thermostat control through web interface
- **Technology**: Python with Selenium WebDriver
- **Target**: Web UI automation for heating system status changes

## Development Guidelines
- Use Python 3.8+ with type hints
- Follow PEP 8 style guidelines
- Include proper error handling and logging
- Use environment variables for sensitive configuration
- Implement retry logic for web interactions
- Add comprehensive documentation and comments

## Security Considerations
- Never commit credentials or API keys
- Use environment variables for configuration
- Implement secure credential storage
- Add rate limiting to prevent abuse

## Testing Strategy
- Include unit tests for core functions
- Test with mock web responses
- Validate error handling scenarios
- Test configuration loading

## Deployment Notes
- Support for headless browser operation
- Configurable delays for web interactions
- Cross-platform compatibility (Windows, macOS, Linux)