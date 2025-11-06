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


def cmd_main_floor_aux(args, automation: EcobeeAutomation) -> int:
    """Set Main Floor thermostat heating mode to Aux."""
    try:
        if automation.set_main_floor_aux():
            print(f"Successfully set Main Floor to: aux")
            return 0
        else:
            print(f"Failed to set Main Floor to: aux")
            return 1
    except Exception as e:
        print(f"Error setting mode: {e}")
        return 1


def cmd_main_floor_heat(args, automation: EcobeeAutomation) -> int:
    """Set Main Floor thermostat heating mode to Heat."""
    try:
        if automation.set_main_floor_heat():
            print(f"Successfully set Main Floor to: heat")
            return 0
        else:
            print(f"Failed to set Main Floor to: heat")
            return 1
    except Exception as e:
        print(f"Error setting mode: {e}")
        return 1


def cmd_upstairs_aux(args, automation: EcobeeAutomation) -> int:
    """Set Upstairs thermostat heating mode to Aux."""
    try:
        if automation.set_upstairs_aux():
            print(f"Successfully set Upstairs to: aux")
            return 0
        else:
            print(f"Failed to set Upstairs to: aux")
            return 1
    except Exception as e:
        print(f"Error setting mode: {e}")
        return 1


def cmd_upstairs_heat(args, automation: EcobeeAutomation) -> int:
    """Set Upstairs thermostat heating mode to Heat."""
    try:
        if automation.set_upstairs_heat():
            print(f"Successfully set Upstairs to: heat")
            return 0
        else:
            print(f"Failed to set Upstairs to: heat")
            return 1
    except Exception as e:
        print(f"Error setting mode: {e}")
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
    parser = argparse.ArgumentParser(
        description='Ecobee Web Automation CLI - Control heating mode for both thermostats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s main-floor-aux           # Set Main Floor to Aux
  %(prog)s main-floor-heat          # Set Main Floor to Heat
  %(prog)s upstairs-aux             # Set Upstairs to Aux
  %(prog)s upstairs-heat            # Set Upstairs to Heat
  %(prog)s --headless=true main-floor-aux  # Set Main Floor to Aux with headless browser
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
    
    # Main Floor Aux command
    main_floor_aux_parser = subparsers.add_parser('main-floor-aux', help='Set Main Floor heating mode to Aux')
    
    # Main Floor Heat command
    main_floor_heat_parser = subparsers.add_parser('main-floor-heat', help='Set Main Floor heating mode to Heat')
    
    # Upstairs Aux command
    upstairs_aux_parser = subparsers.add_parser('upstairs-aux', help='Set Upstairs heating mode to Aux')
    
    # Upstairs Heat command
    upstairs_heat_parser = subparsers.add_parser('upstairs-heat', help='Set Upstairs heating mode to Heat')
    
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
        has_credentials = config.get('ecobee.username') is not None and config.get('ecobee.password') is not None
        
        if not has_credentials:
            logger.error("Configuration error: No credentials configured")
            logger.error("Please set ECOBEE_USERNAME and ECOBEE_PASSWORD in your .secrets file")
            logger.error("(Create /Users/jakuboleksy/github/ecobee.control/.secrets if it doesn't exist)")
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
            if args.command == 'main-floor-aux':
                return cmd_main_floor_aux(args, automation)
            elif args.command == 'main-floor-heat':
                return cmd_main_floor_heat(args, automation)
            elif args.command == 'upstairs-aux':
                return cmd_upstairs_aux(args, automation)
            elif args.command == 'upstairs-heat':
                return cmd_upstairs_heat(args, automation)
            else:
                logger.error(f"Unknown command: {args.command}")
                return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())