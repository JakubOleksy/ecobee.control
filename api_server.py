#!/usr/bin/env python3
"""
REST API Server for Ecobee Automation - Home Assistant Add-on version

Provides REST endpoints for Home Assistant integration.
"""

from flask import Flask, jsonify, render_template_string, request, send_from_directory
import logging
import sys
import os
import threading
import subprocess
import glob
import json
import re
import tempfile
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lock for sequential execution (only one automation at a time)
automation_lock = threading.Lock()

# Path to CLI script
CLI_PATH = os.path.join(os.path.dirname(__file__), 'cli.py')


VERIFICATION_UI = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="5">
  <title>Ecobee Web Control</title>
  <style>
    :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #111827; color: #f9fafb; }
    main { max-width: 34rem; margin: 0 auto; padding: 3rem 1.25rem; }
    .card { background: #1f2937; border: 1px solid #374151; border-radius: 1rem; padding: 1.5rem; box-shadow: 0 12px 30px #0005; }
    h1 { margin-top: 0; font-size: 1.5rem; }
    .status { color: #9ca3af; line-height: 1.5; }
    .waiting { color: #fbbf24; font-weight: 700; }
    .success { color: #6ee7b7; font-weight: 700; }
    .error { color: #fca5a5; font-weight: 700; }
    label { display: block; margin: 1.25rem 0 .5rem; font-weight: 700; }
    input { box-sizing: border-box; width: 100%; font: inherit; font-size: 1.5rem; letter-spacing: .35rem; padding: .8rem 1rem; border: 1px solid #6b7280; border-radius: .6rem; background: #111827; color: #fff; }
    button { margin-top: 1rem; width: 100%; padding: .85rem 1rem; border: 0; border-radius: .6rem; background: #10b981; color: #06291f; font: inherit; font-weight: 800; cursor: pointer; }
    small { display: block; margin-top: 1rem; color: #9ca3af; line-height: 1.4; }
  </style>
</head>
<body>
<main>
  <section class="card">
    <h1>Ecobee Web Control</h1>
    {% if accepted %}
      <p class="success">Code accepted. Ecobee login is continuing.</p>
      <p class="status">This page refreshes automatically.</p>
    {% elif pending %}
      <p class="waiting">Email verification is required.</p>
      <p class="status">Enter the newest six-digit code from Ecobee. This challenge expires in about {{ seconds_remaining }} seconds.</p>
      {% if error %}<p class="error">{{ error }}</p>{% endif %}
      <form method="post" action="">
        <label for="code">Verification code</label>
        <input id="code" name="code" type="text" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" minlength="6" maxlength="6" required autofocus>
        <button type="submit">Continue Ecobee login</button>
      </form>
      <small>The code is accepted only while a login is waiting. It is not displayed or logged.</small>
    {% else %}
      <p class="success">No verification code is needed.</p>
      <p class="status">The Ecobee browser session is ready. If a future login requests email verification, this page will show the code form automatically.</p>
      <small>This page checks for a pending challenge every five seconds.</small>
    {% endif %}
  </section>
</main>
</body>
</html>'''


def get_data_dir():
    """Return the add-on's persistent data directory."""
    return os.environ.get(
        'ECOBEE_DATA_DIR',
        '/data' if os.path.isdir('/data') else os.path.join(os.path.dirname(__file__), 'data')
    )


def get_verification_paths():
    data_dir = get_data_dir()
    os.makedirs(data_dir, exist_ok=True)
    return (
        os.path.join(data_dir, 'email-verification-pending.json'),
        os.path.join(data_dir, 'email-verification-code')
    )


def get_pending_verification():
    """Return active verification metadata, deleting stale state."""
    pending_path, code_path = get_verification_paths()
    try:
        with open(pending_path, 'r') as handle:
            pending = json.load(handle)
        if not pending.get('pending') or int(pending.get('expires_at', 0)) <= int(time.time()):
            raise ValueError('expired')
        return pending
    except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError):
        for path in (pending_path, code_path):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        return None


def write_verification_code(code):
    """Atomically store a six-digit code without putting it in logs."""
    _, code_path = get_verification_paths()
    fd, temp_path = tempfile.mkstemp(prefix='.email-code-', dir=os.path.dirname(code_path))
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(code)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, code_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def validate_and_write_verification_code(code):
    """Validate and store a code for the active challenge."""
    if not get_pending_verification():
        return 'No email verification is pending', 409
    code = str(code or '').strip()
    if not re.fullmatch(r'\d{6}', code):
        return 'Code must be exactly six digits', 400
    write_verification_code(code)
    logger.info("Accepted an emailed Ecobee verification code for the pending login")
    return None, 202


def run_cli_command(command):
    """Run a CLI command and return the result."""
    if not automation_lock.acquire(blocking=False):
        return {'success': False, 'error': 'Another automation is already running'}, 409
    
    try:
        logger.info(f"Executing command: {command}")
        logger.info(f"CLI path: {CLI_PATH}")
        logger.info(f"Working directory: {os.path.dirname(__file__)}")
        
        # Run with combined stderr and stdout
        result = subprocess.run(
            ['python3', CLI_PATH, command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=360,
            cwd=os.path.dirname(__file__)
        )
        
        # Log the full output
        logger.info(f"Command return code: {result.returncode}")
        logger.info(f"Command output:\n{result.stdout}")
        
        if result.returncode == 0:
            logger.info(f"Command succeeded: {command}")
            return {'success': True, 'output': result.stdout}, 200
        else:
            logger.error(f"Command failed with return code {result.returncode}")
            return {'success': False, 'error': result.stdout, 'return_code': result.returncode}, 500
            
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {'success': False, 'error': 'Command timed out'}, 500
    except Exception as e:
        logger.error(f"Error running command: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}, 500
    finally:
        automation_lock.release()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/', methods=['GET', 'POST'])
def verification_ui():
    """Render the add-on UI and accept a code during an active challenge."""
    accepted = False
    error = None
    status = 200
    if request.method == 'POST':
        error, status = validate_and_write_verification_code(request.form.get('code'))
        accepted = error is None

    pending = get_pending_verification()
    seconds_remaining = max(0, int(pending['expires_at']) - int(time.time())) if pending else 0
    response = app.make_response((render_template_string(
        VERIFICATION_UI,
        accepted=accepted,
        pending=bool(pending) and not accepted,
        seconds_remaining=seconds_remaining,
        error=error,
    ), status))
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@app.route('/screenshots', methods=['GET'])
def list_screenshots():
    """List available debug screenshots."""
    screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    if not os.path.exists(screenshots_dir):
        return jsonify({'screenshots': []}), 200
    files = sorted(glob.glob(os.path.join(screenshots_dir, '*.png')), key=os.path.getmtime, reverse=True)
    return jsonify({'screenshots': [os.path.basename(f) for f in files]}), 200


@app.route('/screenshots/<filename>', methods=['GET'])
def get_screenshot(filename):
    """Serve a specific screenshot."""
    screenshots_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
    return send_from_directory(screenshots_dir, filename)


@app.route('/ecobee/verification-status', methods=['GET'])
def verification_status():
    """Report whether a CLI run is waiting for an emailed code."""
    pending = get_pending_verification()
    if not pending:
        return jsonify({'pending': False}), 200
    return jsonify({
        'pending': True,
        'expires_at': pending['expires_at'],
    }), 200


@app.route('/ecobee/verification-code', methods=['POST'])
def verification_code():
    """Accept a six-digit code only while an Ecobee login is waiting."""
    payload = request.get_json(silent=True) or {}
    error, status = validate_and_write_verification_code(payload.get('code'))
    if error:
        return jsonify({'accepted': False, 'error': error}), status
    return jsonify({'accepted': True}), 202


@app.route('/ecobee/main-floor/aux', methods=['POST'])
def main_floor_aux():
    """Set Main Floor thermostat to Aux mode."""
    result, status = run_cli_command('main-floor-aux')
    return jsonify(result), status


@app.route('/ecobee/main-floor/heat', methods=['POST'])
def main_floor_heat():
    """Set Main Floor thermostat to Heat mode."""
    result, status = run_cli_command('main-floor-heat')
    return jsonify(result), status


@app.route('/ecobee/upstairs/aux', methods=['POST'])
def upstairs_aux():
    """Set Upstairs thermostat to Aux mode."""
    result, status = run_cli_command('upstairs-aux')
    return jsonify(result), status


@app.route('/ecobee/upstairs/heat', methods=['POST'])
def upstairs_heat():
    """Set Upstairs thermostat to Heat mode."""
    result, status = run_cli_command('upstairs-heat')
    return jsonify(result), status


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('API_PORT', 5000))
    host = '0.0.0.0'
    
    logger.info(f"Starting Ecobee API server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  POST /ecobee/main-floor/aux   - Set Main Floor to Aux")
    logger.info("  POST /ecobee/main-floor/heat  - Set Main Floor to Heat")
    logger.info("  POST /ecobee/upstairs/aux     - Set Upstairs to Aux")
    logger.info("  POST /ecobee/upstairs/heat    - Set Upstairs to Heat")
    logger.info("  GET  /                         - Email verification UI")
    logger.info("  GET  /health                  - Health check")
    logger.info("  GET  /ecobee/verification-status - Email verification state")
    logger.info("  POST /ecobee/verification-code   - Submit pending six-digit code")
    
    app.run(host=host, port=port, debug=False)
