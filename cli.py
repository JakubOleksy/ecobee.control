#!/usr/bin/env python3
"""
Command Line Interface for Ecobee Automation

Provides a simple CLI for common ecobee automation tasks.
"""

import argparse
import logging
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config_manager import ConfigManager
from src.ecobee_automation import EcobeeAutomation
from src.exceptions import EcobeeAutomationError


def setup_logging(log_level: str = 'INFO'):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def cmd_status(args, automation: EcobeeAutomation) -> int:
    """Get and display current thermostat status."""
    try:
        status = automation.get_heating_status()
        
        print("=== Ecobee Thermostat Status ===")
        print(f"Current Temperature: {status.current_temp}°F" if status.current_temp else "Current Temperature: Unknown")
        print(f"Target Temperature:  {status.target_temp}°F" if status.target_temp else "Target Temperature: Unknown")
        print(f"Mode:                {status.mode}" if status.mode else "Mode: Unknown")
        print(f"Heating Active:      {status.is_heating}" if status.is_heating is not None else "Heating Active: Unknown")
        
        return 0
        
    except Exception as e:
        print(f"Error getting status: {e}")
        return 1


def cmd_set_mode(args, automation: EcobeeAutomation) -> int:
    """Set heating mode."""
    try:
        if automation.set_heating_mode(args.mode):
            print(f"Successfully set mode to: {args.mode}")
            return 0
        else:
            print(f"Failed to set mode to: {args.mode}")
            return 1
            
    except Exception as e:
        print(f"Error setting mode: {e}")
        return 1


def cmd_set_temp(args, automation: EcobeeAutomation) -> int:
    """Set target temperature."""
    try:
        if automation.set_temperature(args.temperature):
            print(f"Successfully set temperature to: {args.temperature}°F")
            return 0
        else:
            print(f"Failed to set temperature to: {args.temperature}°F")
            return 1
            
    except Exception as e:
        print(f"Error setting temperature: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Ecobee Web Automation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Get current thermostat status
  %(prog)s set-mode heat            # Set heating mode to 'heat'
  %(prog)s set-temp 72              # Set target temperature to 72°F
  %(prog)s --headless=false status  # Run with visible browser
        """
    )
    
    # Global options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--headless', type=str, choices=['true', 'false'],
                       help='Run browser in headless mode')
    parser.add_argument('--config-dir', help='Path to configuration directory')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get current thermostat status')
    
    # Set mode command
    mode_parser = subparsers.add_parser('set-mode', help='Set heating mode')
    mode_parser.add_argument('mode', choices=['heat', 'cool', 'auto', 'off'],
                           help='Heating mode to set')
    
    # Set temperature command
    temp_parser = subparsers.add_parser('set-temp', help='Set target temperature')
    temp_parser.add_argument('temperature', type=float,
                           help='Target temperature in Fahrenheit')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Load configuration
        config = ConfigManager(args.config_dir)
        
        # Override headless setting if specified
        if args.headless:
            config.set('webdriver.headless', args.headless.lower() == 'true')
        
        # Validate required configuration
        required_config = ['ecobee.username', 'ecobee.password']
        try:
            config.validate_required(required_config)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            logger.error("Please set ECOBEE_USERNAME and ECOBEE_PASSWORD in your .env file")
            return 1
        
        # Run automation
        with EcobeeAutomation(config) as automation:
            # Login
            logger.info("Logging into ecobee...")
            if not automation.login():
                logger.error("Failed to login to ecobee")
                return 1
            
            logger.info("Login successful")
            
            # Execute command
            if args.command == 'status':
                return cmd_status(args, automation)
            elif args.command == 'set-mode':
                return cmd_set_mode(args, automation)
            elif args.command == 'set-temp':
                return cmd_set_temp(args, automation)
            else:
                logger.error(f"Unknown command: {args.command}")
                return 1
                
    except EcobeeAutomationError as e:
        logger.error(f"Automation error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())