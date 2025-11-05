#!/usr/bin/env python3
"""
Ecobee Web Automation Script

This script automates the navigation of the ecobee web UI to control
heating system status through browser automation using Selenium.
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config_manager import ConfigManager
from src.exceptions import EcobeeAutomationError


@dataclass
class HeatingStatus:
    """Data class to represent heating system status."""
    current_temp: Optional[float] = None
    target_temp: Optional[float] = None
    mode: Optional[str] = None
    is_heating: Optional[bool] = None


class EcobeeAutomation:
    """Main class for automating ecobee web interface interactions."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the automation with configuration."""
        self.config = config_manager
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.logger = logging.getLogger(__name__)
        
        # Ecobee web interface URLs and selectors
        self.login_url = "https://www.ecobee.com/consumerportal/index.html"
        self.portal_url = "https://www.ecobee.com/home/index.html"
        
        # Common selectors (these may need to be updated based on actual UI)
        self.selectors = {
            'username_field': '#userName',
            'password_field': '#password', 
            'login_button': '#loginButton',
            'thermostat_card': '.thermostat-card',
            'current_temp': '.current-temp',
            'target_temp': '.target-temp',
            'mode_selector': '.mode-selector',
            'heating_mode': '[data-mode="heat"]',
            'cooling_mode': '[data-mode="cool"]',
            'auto_mode': '[data-mode="auto"]',
            'off_mode': '[data-mode="off"]',
            'temp_up': '.temp-up',
            'temp_down': '.temp-down',
            'save_button': '.save-changes'
        }

    def setup_driver(self) -> None:
        """Set up Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            
            if self.config.get('webdriver.headless', True):
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set timeouts
            self.driver.implicitly_wait(self.config.get('webdriver.implicit_wait', 10))
            self.driver.set_page_load_timeout(self.config.get('webdriver.page_load_timeout', 30))
            
            self.wait = WebDriverWait(self.driver, 10)
            self.logger.info("WebDriver setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            raise EcobeeAutomationError(f"WebDriver setup failed: {e}")

    def login(self) -> bool:
        """Log into the ecobee web portal."""
        try:
            self.logger.info("Attempting to log into ecobee portal")
            
            self.driver.get(self.login_url)
            time.sleep(self.config.get('automation.delay', 2))
            
            # Wait for and fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['username_field']))
            )
            username_field.clear()
            username_field.send_keys(self.config.get('ecobee.username'))
            
            # Fill password
            password_field = self.driver.find_element(By.CSS_SELECTOR, self.selectors['password_field'])
            password_field.clear()
            password_field.send_keys(self.config.get('ecobee.password'))
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['login_button'])
            login_button.click()
            
            # Wait for login to complete
            self.wait.until(lambda driver: driver.current_url != self.login_url)
            
            self.logger.info("Login successful")
            return True
            
        except TimeoutException:
            self.logger.error("Login timed out")
            self._take_screenshot("login_timeout")
            return False
        except NoSuchElementException as e:
            self.logger.error(f"Login element not found: {e}")
            self._take_screenshot("login_element_error")
            return False
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            self._take_screenshot("login_error")
            return False

    def get_heating_status(self) -> HeatingStatus:
        """Get current heating system status."""
        try:
            self.logger.info("Retrieving heating system status")
            
            # Navigate to thermostat control page if not already there
            if self.portal_url not in self.driver.current_url:
                self.driver.get(self.portal_url)
                time.sleep(self.config.get('automation.delay', 2))
            
            status = HeatingStatus()
            
            # Get current temperature
            try:
                current_temp_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors['current_temp'])
                temp_text = current_temp_element.text.replace('°', '').replace('F', '').strip()
                status.current_temp = float(temp_text)
            except (NoSuchElementException, ValueError) as e:
                self.logger.warning(f"Could not get current temperature: {e}")
            
            # Get target temperature
            try:
                target_temp_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors['target_temp'])
                temp_text = target_temp_element.text.replace('°', '').replace('F', '').strip()
                status.target_temp = float(temp_text)
            except (NoSuchElementException, ValueError) as e:
                self.logger.warning(f"Could not get target temperature: {e}")
            
            # Get current mode
            try:
                mode_element = self.driver.find_element(By.CSS_SELECTOR, self.selectors['mode_selector'])
                status.mode = mode_element.get_attribute('data-current-mode') or mode_element.text.lower()
            except NoSuchElementException as e:
                self.logger.warning(f"Could not get current mode: {e}")
            
            # Determine if heating is active
            if status.current_temp and status.target_temp:
                status.is_heating = status.current_temp < status.target_temp and status.mode in ['heat', 'auto']
            
            self.logger.info(f"Retrieved status: {status}")
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get heating status: {e}")
            self._take_screenshot("status_error")
            raise EcobeeAutomationError(f"Status retrieval failed: {e}")

    def set_heating_mode(self, mode: str) -> bool:
        """Set the heating system mode (heat, cool, auto, off)."""
        try:
            self.logger.info(f"Setting heating mode to: {mode}")
            
            mode = mode.lower()
            if mode not in ['heat', 'cool', 'auto', 'off']:
                raise ValueError(f"Invalid mode: {mode}. Must be one of: heat, cool, auto, off")
            
            # Click the appropriate mode button
            mode_selector = f"{mode}_mode"
            if mode_selector not in self.selectors:
                raise ValueError(f"No selector found for mode: {mode}")
            
            mode_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.selectors[mode_selector]))
            )
            mode_button.click()
            
            time.sleep(self.config.get('automation.delay', 2))
            
            # Save changes if save button exists
            try:
                save_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['save_button'])
                save_button.click()
                time.sleep(self.config.get('automation.delay', 2))
            except NoSuchElementException:
                # Some interfaces auto-save
                pass
            
            self.logger.info(f"Successfully set mode to: {mode}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set heating mode: {e}")
            self._take_screenshot("mode_change_error")
            return False

    def set_temperature(self, temperature: float) -> bool:
        """Set the target temperature."""
        try:
            self.logger.info(f"Setting target temperature to: {temperature}°F")
            
            current_status = self.get_heating_status()
            if not current_status.target_temp:
                raise EcobeeAutomationError("Could not retrieve current target temperature")
            
            temp_diff = temperature - current_status.target_temp
            
            if abs(temp_diff) < 0.5:  # Already at target temperature
                self.logger.info("Temperature already at target")
                return True
            
            # Click temp up or down buttons to reach target
            button_selector = self.selectors['temp_up'] if temp_diff > 0 else self.selectors['temp_down']
            clicks_needed = abs(int(temp_diff))
            
            temp_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
            )
            
            for _ in range(clicks_needed):
                temp_button.click()
                time.sleep(0.5)  # Small delay between clicks
            
            # Save changes
            try:
                save_button = self.driver.find_element(By.CSS_SELECTOR, self.selectors['save_button'])
                save_button.click()
                time.sleep(self.config.get('automation.delay', 2))
            except NoSuchElementException:
                pass
            
            self.logger.info(f"Successfully set temperature to: {temperature}°F")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set temperature: {e}")
            self._take_screenshot("temp_change_error")
            return False

    def _take_screenshot(self, name: str) -> None:
        """Take a screenshot for debugging purposes."""
        if not self.config.get('automation.screenshot_on_error', True) or not self.driver:
            return
        
        try:
            screenshots_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"{name}_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            self.driver.save_screenshot(filepath)
            self.logger.info(f"Screenshot saved: {filepath}")
            
        except Exception as e:
            self.logger.warning(f"Failed to take screenshot: {e}")

    def close(self) -> None:
        """Clean up and close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Main function to demonstrate automation usage."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/ecobee_automation.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        
        # Validate required configuration
        required_config = ['ecobee.username', 'ecobee.password']
        for key in required_config:
            if not config_manager.get(key):
                raise ValueError(f"Missing required configuration: {key}")
        
        # Run automation
        with EcobeeAutomation(config_manager) as automation:
            # Login
            if not automation.login():
                logger.error("Failed to login")
                return 1
            
            # Get current status
            status = automation.get_heating_status()
            logger.info(f"Current status: {status}")
            
            # Example: Set heating mode and temperature
            # automation.set_heating_mode('heat')
            # automation.set_temperature(72.0)
            
        logger.info("Automation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())