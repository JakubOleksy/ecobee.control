# Home Assistant Add-on: Ecobee Web Control

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Control your Ecobee thermostats through web automation - no API key required!

## About

This add-on provides a REST API to control Ecobee thermostats by automating the web interface. It uses Selenium and headless Chrome to log in to your Ecobee account and change thermostat modes.

Perfect for:
- Switching between Heat and Aux Heat modes
- Automating thermostat control based on time or conditions
- Controlling multiple thermostats
- Bypassing API limitations or developer account requirements

## Installation

1. Click the Home Assistant My button below to open the add-on on your instance:

   [![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FJakubOleksy%2Fecobee.control)

2. Or manually add the repository:
   - Navigate to **Supervisor** → **Add-on Store**
   - Click the 3-dot menu → **Repositories**
   - Add: `https://github.com/JakubOleksy/ecobee.control`
   - Find "Ecobee Web Control" and click **Install**

3. Configure the add-on with your Ecobee credentials
4. Start the add-on
5. Check the logs to verify it started successfully

## Configuration

Example add-on configuration:

```yaml
ecobee_username: your-email@example.com
ecobee_password: your-password
webdriver_headless: true
log_level: INFO
api_port: 5000
```

## Home Assistant Integration

After the add-on is running, add these to your `configuration.yaml`:

```yaml
rest_command:
  ecobee_main_floor_aux:
    url: "http://localhost:5000/ecobee/main-floor/aux"
    method: POST
    
  ecobee_main_floor_heat:
    url: "http://localhost:5000/ecobee/main-floor/heat"
    method: POST
    
  ecobee_upstairs_aux:
    url: "http://localhost:5000/ecobee/upstairs/aux"
    method: POST
    
  ecobee_upstairs_heat:
    url: "http://localhost:5000/ecobee/upstairs/heat"
    method: POST
```

Then restart Home Assistant and use the commands in your automations!

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/JakubOleksy/ecobee.control/issues

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
