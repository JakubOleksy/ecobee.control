# Changelog

All notable changes to this add-on will be documented in this file.

## [1.2.0] - 2026-09-20

### Fixed
- Handle Ecobee/Auth0's emailed six-digit verification prompt.
- Persist the Chrome profile under `/data` so verified sessions survive one-shot commands, restarts, and rebuilds.
- Try the consumer portal before starting a new credential login.

### Added
- Short-lived verification status and code-submission endpoints; codes are never logged or echoed.

## [1.0.0] - 2025-11-05

### Added
- Initial release
- Support for Main Floor thermostat
- Support for Upstairs thermostat
- REST API with four endpoints (aux/heat for each thermostat)
- Automated web login and control
- Headless Chrome/Selenium automation
- Health check endpoint
