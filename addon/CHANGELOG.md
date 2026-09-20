# Changelog

All notable changes to this add-on will be documented in this file.

## [1.2.3] - 2026-09-20

### Fixed
+- Resume an email-verification page left in the persistent browser profile before searching for username controls.
+- Choose the email page's Continue button explicitly instead of its Resend submit control.
+
## [1.2.2] - 2026-09-20

### Fixed
+- Submit the visible Auth0 Continue button instead of a hidden submit control on the email-code page.
+
## [1.2.1] - 2026-09-20

### Fixed
+- Validate a saved session through the Auth0 login route; the legacy consumer-portal URL can render a blank page without redirecting.
+
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
