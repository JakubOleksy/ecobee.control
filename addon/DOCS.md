# Ecobee Web Control Add-on

Control your Ecobee thermostats directly through the web interface using Selenium automation. No API key required!

## Features

- ✅ Control multiple thermostats (Main Floor and Upstairs)
- ✅ Switch between Heat and Aux Heat modes
- ✅ No API key or developer account needed
- ✅ Works with standard Ecobee web login credentials
- ✅ Runs completely local in your Home Assistant
- ✅ Reuses a persistent browser login across commands and add-on rebuilds
- ✅ Supports Ecobee's emailed six-digit verification challenge
- ✅ Provides a Home Assistant add-on UI for manual email-code entry
- ✅ Surfaces failures as Home Assistant notifications and System Log errors

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Ecobee Web Control" add-on
3. Configure your Ecobee credentials in the add-on configuration
4. Start the add-on
5. Add the REST commands to your Home Assistant configuration (see below)

## Configuration

### Add-on Configuration

```yaml
ecobee_username: your-email@example.com
ecobee_password: your-password
webdriver_headless: true
log_level: INFO
api_port: 5000
```

### Home Assistant Configuration

Add this to your `configuration.yaml`:

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

script:
  set_main_floor_to_aux:
    alias: "Set Main Floor to Aux Heat"
    sequence:
      - service: rest_command.ecobee_main_floor_aux
  
  set_main_floor_to_heat:
    alias: "Set Main Floor to Heat"
    sequence:
      - service: rest_command.ecobee_main_floor_heat
  
  set_upstairs_to_aux:
    alias: "Set Upstairs to Aux Heat"
    sequence:
      - service: rest_command.ecobee_upstairs_aux
  
  set_upstairs_to_heat:
    alias: "Set Upstairs to Heat"
    sequence:
      - service: rest_command.ecobee_upstairs_heat
```

## Usage

After setup, you can call these scripts from automations, dashboards, or voice assistants:

```yaml
# Example automation
automation:
  - alias: "Morning Heat"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: script.set_main_floor_to_heat
      - service: script.set_upstairs_to_heat
```

## API Endpoints

The add-on exposes these REST endpoints:

- `POST /ecobee/main-floor/aux` - Set Main Floor to Aux Heat
- `POST /ecobee/main-floor/heat` - Set Main Floor to Heat
- `POST /ecobee/upstairs/aux` - Set Upstairs to Aux Heat
- `POST /ecobee/upstairs/heat` - Set Upstairs to Heat
- `GET /health` - Health check
- `GET /ecobee/verification-status` - Check whether a login is awaiting an emailed code
- `POST /ecobee/verification-code` - Submit `{"code":"123456"}` while verification is pending

## First Login or Reverification

When Ecobee requires a new-browser verification, the thermostat command waits
for up to five minutes. Open the add-on page and select **Open Web UI**. The UI
refreshes automatically and shows a six-digit form while verification is
pending. Enter the newest code from Ecobee's email and select **Continue Ecobee
login**.

The same flow is available through the REST API:

```bash
curl http://HOME_ASSISTANT_IP:5000/ecobee/verification-status
curl -X POST -H 'Content-Type: application/json' \
  -d '{"code":"123456"}' \
  http://HOME_ASSISTANT_IP:5000/ecobee/verification-code
```

The code is accepted only while a verification challenge is active, is stored briefly with restrictive permissions, and is not logged, displayed, or returned. After verification, the add-on reuses its browser profile so normal automation does not require another code.

## Home Assistant Error Reporting

When email verification is required, Home Assistant displays an actionable persistent notification that points to **Ecobee Web Control → Open Web UI**.

A thermostat-command failure, timeout, concurrency conflict, or unexpected API error:

1. Creates or updates a persistent **Ecobee** notification.
2. Writes an `ecobee_web_control` error to **Settings → System → Logs**.
3. Keeps detailed browser diagnostics in the add-on log without putting credentials or verification codes in the Home Assistant message.

A later successful thermostat command dismisses active Ecobee notifications. System Log entries remain available as historical evidence.

## Support

For issues and questions: https://github.com/JakubOleksy/ecobee.control/issues
