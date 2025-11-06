#!/usr/bin/env python3
"""
REST API Server for Ecobee Automation - Home Assistant Add-on version

Provides REST endpoints for Home Assistant integration.
"""

from flask import Flask, jsonify
import logging
import sys
import os
import threading
import subprocess

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
            timeout=120,
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
    logger.info("  GET  /health                  - Health check")
    
    app.run(host=host, port=port, debug=False)
