# Ecobee Web Control

A Python-based automation tool for controlling ecobee thermostats through the web interface using Selenium WebDriver. Available as a Home Assistant Add-on or standalone CLI tool.

## Features

- **Home Assistant Integration**: Available as a Home Assistant add-on with REST API
- **Multiple Thermostats**: Control Main Floor and Upstairs thermostats independently
- **Web UI Automation**: Automated navigation of the ecobee web portal
- **Mode Switching**: Switch between Heat and Aux Heat modes
- **Headless Operation**: Runs in background without visible browser
- **Robust Error Handling**: Comprehensive error handling with retry logic
- **Configurable Settings**: Flexible configuration through environment variables and YAML files
- **Logging**: Detailed logging for debugging and monitoring
- **Screenshot Capture**: Automatic screenshots on errors for debugging

## Installation Options

### Option 1: Home Assistant Add-on (Recommended)

1. Add this repository to your Home Assistant add-on store:
   - Navigate to **Supervisor** → **Add-on Store**
   - Click the 3-dot menu → **Repositories**
   - Add: `https://github.com/JakubOleksy/ecobee.control`
   - Find "Ecobee Web Control" and click **Install**

2. Configure the add-on with your Ecobee credentials
3. Start the add-on
4. Add REST commands to your `configuration.yaml` (see [addon/DOCS.md](addon/DOCS.md))

### Option 2: Standalone CLI Tool

```
ecobee.control/
├── addon/                       # Home Assistant Add-on files
│   ├── config.yaml             # Add-on configuration
│   ├── Dockerfile              # Container build instructions
│   ├── run.sh                  # Add-on startup script
│   ├── DOCS.md                 # Add-on documentation
│   └── README.md               # Add-on readme
├── .github/
│   └── copilot-instructions.md  # Project guidelines and instructions
├── src/
│   ├── __init__.py              # Package initialization
│   ├── ecobee_automation.py     # Main automation class
│   ├── config_manager.py        # Configuration management
│   └── exceptions.py            # Custom exception classes
├── config/
│   └── default.yml              # Default configuration settings
├── cli.py                       # Command-line interface
├── api_server.py                # REST API server (for add-on)
├── requirements.txt             # Python dependencies
├── .env                         # Environment configuration
├── .secrets                     # Credentials (gitignored)
├── repository.json              # Home Assistant repository config
└── README.md                   # This file
```

## Prerequisites (Standalone CLI)

## Project Structure

- Python 3.8 or higher
- Chrome browser installed
- Valid ecobee account with web portal access

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JakubOleksy/ecobee-web-automation.git
   cd ecobee-web-automation
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up configuration**:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` and add your ecobee credentials:
   ```
   ECOBEE_USERNAME=your_username_here
   ECOBEE_PASSWORD=your_password_here
   ```

## Configuration

The application uses a layered configuration system:

1. **Default settings**: `config/default.yml`
2. **Environment variables**: `.env` file or system environment
3. **Local overrides**: `config/local.yml` (optional, gitignored)

### Key Configuration Options

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| `ecobee.username` | `ECOBEE_USERNAME` | - | Your ecobee username |
| `ecobee.password` | `ECOBEE_PASSWORD` | - | Your ecobee password |
| `webdriver.headless` | `WEBDRIVER_HEADLESS` | `true` | Run browser in headless mode |
| `automation.delay` | `AUTOMATION_DELAY` | `2` | Delay between actions (seconds) |
| `automation.screenshot_on_error` | `SCREENSHOT_ON_ERROR` | `true` | Take screenshots on errors |

## Usage

### Basic Usage

```python
from src.config_manager import ConfigManager
from src.ecobee_automation import EcobeeAutomation

# Load configuration
config = ConfigManager()

# Use the automation
with EcobeeAutomation(config) as automation:
    # Login to ecobee
    if automation.login():
        # Get current status
        status = automation.get_heating_status()
        print(f"Current temp: {status.current_temp}°F")
        print(f"Target temp: {status.target_temp}°F")
        print(f"Mode: {status.mode}")
        
        # Change heating mode
        automation.set_heating_mode('heat')
        
        # Set target temperature
        automation.set_temperature(72.0)
```

### Command Line Usage

Run the main script directly:

```bash
python src/ecobee_automation.py
```

### Available Methods

#### `EcobeeAutomation` Class Methods

- **`login()`**: Authenticate with ecobee web portal
- **`get_heating_status()`**: Retrieve current thermostat status
- **`set_heating_mode(mode)`**: Change heating mode (`'heat'`, `'cool'`, `'auto'`, `'off'`)
- **`set_temperature(temp)`**: Set target temperature (in Fahrenheit)

#### `HeatingStatus` Data Class

Contains current thermostat information:
- `current_temp`: Current temperature reading
- `target_temp`: Target temperature setting
- `mode`: Current heating/cooling mode
- `is_heating`: Whether system is actively heating

## Development

### Adding New Features

1. **Web Element Selectors**: Update selectors in `config/default.yml` if ecobee changes their UI
2. **New Automation Methods**: Add methods to `EcobeeAutomation` class
3. **Configuration Options**: Add new settings to config files and environment mappings

### Testing

Create unit tests in the `tests/` directory:

```python
# tests/test_config_manager.py
import unittest
from src.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_config_loading(self):
        config = ConfigManager()
        self.assertIsNotNone(config.get('webdriver.headless'))
```

Run tests:
```bash
python -m pytest tests/
```

### Debugging

1. **Enable Screenshots**: Set `SCREENSHOT_ON_ERROR=true` in `.env`
2. **Disable Headless Mode**: Set `WEBDRIVER_HEADLESS=false` to see browser actions
3. **Increase Logging**: Set `LOG_LEVEL=DEBUG` for detailed logs
4. **Check Logs**: Review logs in `logs/ecobee_automation.log`

## Security Considerations

- **Never commit credentials**: Use environment variables for sensitive data
- **Use strong passwords**: Enable 2FA on your ecobee account if available
- **Rate limiting**: Avoid too frequent automation runs to prevent account lockout
- **Private repository**: Keep your automation code private to protect selectors and logic

## Troubleshooting

### Common Issues

1. **Login Failures**:
   - Verify credentials in `.env` file
   - Check if ecobee has changed their login flow
   - Enable 2FA bypass for automation if needed

2. **Element Not Found Errors**:
   - Ecobee may have updated their UI
   - Update selectors in `config/default.yml`
   - Take screenshots to see current page state

3. **WebDriver Issues**:
   - Update Chrome browser to latest version
   - Clear Chrome user data if needed
   - Check ChromeDriver compatibility

4. **Network Timeouts**:
   - Increase timeout values in configuration
   - Check internet connection stability
   - Verify ecobee service availability

### Error Handling

The application includes comprehensive error handling:

- **Automatic retries** for transient failures
- **Screenshot capture** on errors for debugging
- **Detailed logging** with timestamps and context
- **Graceful degradation** when non-critical operations fail

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with appropriate tests
4. Update documentation if needed
5. Submit a pull request

## License

This project is for personal use. Ensure compliance with ecobee's terms of service when using this automation.

## Disclaimer

This tool is for educational and personal automation purposes. Users are responsible for:
- Complying with ecobee's terms of service
- Securing their account credentials
- Using automation responsibly
- Any consequences of automated actions

The authors are not responsible for any damages or service disruptions caused by this tool.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in `logs/ecobee_automation.log`
3. Create an issue in the GitHub repository with:
   - Error messages and logs
   - Steps to reproduce
   - Configuration details (without credentials)
   - Screenshots if helpful