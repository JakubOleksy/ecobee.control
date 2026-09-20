"""Surface Ecobee automation failures in Home Assistant."""

import json
import logging
import os
import urllib.error
import urllib.request


logger = logging.getLogger(__name__)
SUPERVISOR_CORE_API = "http://supervisor/core/api"
ERROR_NOTIFICATION_ID = "ecobee_web_control_error"
VERIFICATION_NOTIFICATION_ID = "ecobee_web_control_verification"


def _supervisor_token():
    return os.environ.get("SUPERVISOR_TOKEN")


def reporting_available():
    """Prove that the add-on can reach the Home Assistant Core API."""
    token = _supervisor_token()
    if not token:
        return False
    request = urllib.request.Request(
        f"{SUPERVISOR_CORE_API}/",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        logger.warning("Home Assistant error reporting is unavailable: %s", error)
        return False


def _call_service(domain, service, payload):
    """Call a Home Assistant service through the Supervisor proxy."""
    token = _supervisor_token()
    if not token:
        logger.debug("SUPERVISOR_TOKEN is unavailable; skipping Home Assistant notification")
        return False

    request = urllib.request.Request(
        f"{SUPERVISOR_CORE_API}/services/{domain}/{service}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        logger.warning("Could not surface Ecobee status in Home Assistant: %s", error)
        return False


def notify_verification_required():
    """Show an actionable notification while Auth0 waits for an email code."""
    return _call_service("persistent_notification", "create", {
        "notification_id": VERIFICATION_NOTIFICATION_ID,
        "title": "Ecobee email verification required",
        "message": (
            "An Ecobee thermostat command is waiting for the six-digit code "
            "sent by email. Open **Ecobee Web Control → Open Web UI** and "
            "enter the newest code."
        ),
    })


def report_error(title, message):
    """Create a visible notification and a historical Home Assistant error log."""
    visible = _call_service("persistent_notification", "create", {
        "notification_id": ERROR_NOTIFICATION_ID,
        "title": title,
        "message": message,
    })
    logged = _call_service("system_log", "write", {
        "level": "error",
        "logger": "ecobee_web_control",
        "message": f"{title}: {message}",
    })
    return visible or logged


def clear_notifications():
    """Dismiss active Ecobee notifications after a successful command."""
    results = []
    for notification_id in (ERROR_NOTIFICATION_ID, VERIFICATION_NOTIFICATION_ID):
        results.append(_call_service("persistent_notification", "dismiss", {
            "notification_id": notification_id,
        }))
    return any(results)
