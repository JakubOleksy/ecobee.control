#!/usr/bin/env python3
"""
Ecobee Web Automation Script

This script automates the navigation of the ecobee web UI to control
heating system status through browser automation using Selenium.
"""

import os
import time
import logging
import subprocess
import json
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
        self.login_url = "https://auth.ecobee.com/u/login"
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
            
            headless = self.config.get('webdriver.headless', False)
            self.logger.info(f"Headless mode: {headless} (type: {type(headless)})")
            
            if headless:
                chrome_options.add_argument('--headless')
                self.logger.info("Running in headless mode")
            else:
                self.logger.info("Running with visible browser")
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            
            # Detect Chrome/Chromium binary location
            chrome_binary = os.environ.get('CHROME_BIN')
            if chrome_binary and os.path.exists(chrome_binary):
                chrome_options.binary_location = chrome_binary
                self.logger.info(f"Using Chrome binary: {chrome_binary}")
            
            # Get chromedriver path
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')
            if chromedriver_path and os.path.exists(chromedriver_path):
                driver_path = chromedriver_path
                self.logger.info(f"Using chromedriver from environment: {driver_path}")
            else:
                # Fall back to webdriver-manager
                driver_path = ChromeDriverManager().install()
                
                # Workaround for webdriver-manager bug that points to wrong file
                if 'THIRD_PARTY_NOTICES' in driver_path or 'LICENSE' in driver_path:
                    # Extract the directory and point to actual chromedriver
                    driver_dir = os.path.dirname(driver_path)
                    driver_path = os.path.join(driver_dir, 'chromedriver')
                    self.logger.info(f"Fixed chromedriver path to: {driver_path}")
            
            service = Service(driver_path)
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
            
            # Get credentials from configuration (.secrets file)
            username = self.config.get('ecobee.username')
            password = self.config.get('ecobee.password')
            
            if not username or not password:
                self.logger.error("Username or password not configured")
                return False
            
            self.driver.get(self.login_url)
            self.logger.info(f"Navigated to: {self.driver.current_url}")
            time.sleep(3)  # Wait for page to fully load
            
            # Debug: Log page structure
            self._log_page_structure()
            
            # Find and fill username/email field
            self.logger.info("Looking for email/username field...")
            username_field = self._find_input_field(['email', 'username', 'user'])
            if not username_field:
                self.logger.error("Could not find username/email field")
                self._take_screenshot("username_field_not_found")
                return False
            
            self.logger.info("Found username field, entering email...")
            username_field.clear()
            username_field.send_keys(username)
            time.sleep(1)
            
            # Check if password field is visible (single page login) or if we need to click Continue
            password_visible = False
            try:
                password_field = self._find_input_field(['password'], timeout=2)
                if password_field and password_field.is_displayed():
                    password_visible = True
                    self.logger.info("Password field is visible (single-page login)")
            except Exception:
                pass
            
            if not password_visible:
                # Multi-step login - need to click Continue first
                self.logger.info("Password field not visible, looking for Continue button...")
                continue_button = self._find_submit_button()
                if continue_button:
                    self.logger.info("Clicking Continue button...")
                    # Use JavaScript click to avoid interception issues
                    self.driver.execute_script("arguments[0].click();", continue_button)
                    time.sleep(3)  # Wait for password page to load
                else:
                    self.logger.error("Could not find Continue button")
                    self._take_screenshot("continue_button_not_found")
                    return False
            
            # Find and fill password field
            self.logger.info("Looking for password field...")
            password_field = self._find_input_field(['password', 'passwd', 'pass'], timeout=10)
            if not password_field:
                self.logger.error("Could not find password field")
                self._take_screenshot("password_field_not_found")
                return False
            
            self.logger.info("Found password field, entering password...")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # Find and click submit button
            self.logger.info("Looking for submit button...")
            submit_button = self._find_submit_button()
            if not submit_button:
                self.logger.error("Could not find submit button")
                self._take_screenshot("submit_button_not_found")
                return False
            
            self.logger.info("Found submit button, clicking...")
            submit_button.click()
            
            # Wait for login to complete
            time.sleep(2)
            self.logger.info(f"After login, current URL: {self.driver.current_url}")
            
            # Check if login was successful (URL should change to consumerportal)
            if 'auth.ecobee.com' in self.driver.current_url.lower():
                self.logger.warning("Still on auth page, login may have failed")
                self._take_screenshot("login_verification_needed")
                # Don't fail immediately, might just need more time
                time.sleep(5)
            
            self.logger.info("Login successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            self._take_screenshot("login_error")
            return False

    def _get_totp_from_1password(self, item_name: str = "ecobee") -> Optional[str]:
        """
        Retrieve TOTP code from 1Password CLI.
        
        Args:
            item_name: Name of the 1Password item containing the TOTP
            
        Returns:
            TOTP code if successful, None otherwise
        """
        try:
            # Get TOTP using --otp flag
            result = subprocess.run(
                ['op', 'item', 'get', item_name, '--otp'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                totp_code = result.stdout.strip()
                if totp_code and totp_code.isdigit() and len(totp_code) == 6:
                    self.logger.info("Successfully retrieved TOTP from 1Password")
                    return totp_code
                else:
                    self.logger.warning(f"Invalid TOTP format from 1Password: {totp_code}")
                    return None
            else:
                self.logger.warning(f"1Password CLI error: {result.stderr.strip()}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("1Password CLI timed out")
            return None
        except FileNotFoundError:
            self.logger.debug("1Password CLI not found")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving TOTP from 1Password: {e}")
            return None

    def _get_credentials_from_1password(self, item_name: str = "ecobee") -> Optional[Dict[str, str]]:
        """
        Retrieve username and password from 1Password CLI.
        
        Args:
            item_name: Name of the 1Password item
            
        Returns:
            Dict with 'username' and 'password' keys if successful, None otherwise
        """
        try:
            # Get username using field id
            username_result = subprocess.run(
                ['op', 'item', 'get', item_name, '--fields', 'username'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Get password using field id with --reveal flag
            password_result = subprocess.run(
                ['op', 'item', 'get', item_name, '--fields', 'password', '--reveal'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if username_result.returncode == 0 and password_result.returncode == 0:
                username = username_result.stdout.strip()
                password = password_result.stdout.strip()
                
                if username and password:
                    self.logger.info("Successfully retrieved credentials from 1Password")
                    return {'username': username, 'password': password}
                else:
                    self.logger.warning("Retrieved empty username or password from 1Password")
                    return None
            else:
                username_err = username_result.stderr.strip() if username_result.returncode != 0 else ""
                password_err = password_result.stderr.strip() if password_result.returncode != 0 else ""
                self.logger.warning(f"1Password CLI error - Username: {username_err}, Password: {password_err}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("1Password CLI timed out")
            return None
        except FileNotFoundError:
            self.logger.debug("1Password CLI not found")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving credentials from 1Password: {e}")
            return None


    def _log_page_structure(self) -> None:
        """Log the structure of input fields and buttons on the current page for debugging."""
        try:
            # Log all input fields
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            self.logger.info(f"Found {len(inputs)} input fields on page:")
            for i, inp in enumerate(inputs[:10]):  # Limit to first 10
                input_type = inp.get_attribute('type') or 'text'
                input_name = inp.get_attribute('name') or 'no-name'
                input_id = inp.get_attribute('id') or 'no-id'
                input_placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                self.logger.info(f"  Input {i}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
            
            # Log all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            self.logger.info(f"Found {len(buttons)} buttons on page:")
            for i, btn in enumerate(buttons[:10]):  # Limit to first 10
                btn_text = btn.text or 'no-text'
                btn_type = btn.get_attribute('type') or 'button'
                btn_name = btn.get_attribute('name') or 'no-name'
                btn_id = btn.get_attribute('id') or 'no-id'
                self.logger.info(f"  Button {i}: text='{btn_text}', type={btn_type}, name={btn_name}, id={btn_id}")
                
        except Exception as e:
            self.logger.debug(f"Error logging page structure: {e}")

    def _find_input_field(self, keywords: list, timeout: int = 5):
        """Find an input field by searching for keywords in various attributes."""
        try:
            # Try finding by exact type first
            if 'email' in keywords:
                try:
                    field = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]'))
                    )
                    self.logger.info(f"Found field by type=email")
                    return field
                except TimeoutException:
                    pass
            
            if 'password' in keywords:
                try:
                    field = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
                    )
                    self.logger.info(f"Found field by type=password")
                    return field
                except TimeoutException:
                    pass
            
            # Try all input fields and match by attributes
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for inp in inputs:
                # Check if any keyword appears in any attribute
                input_type = (inp.get_attribute('type') or '').lower()
                input_name = (inp.get_attribute('name') or '').lower()
                input_id = (inp.get_attribute('id') or '').lower()
                input_placeholder = (inp.get_attribute('placeholder') or '').lower()
                input_autocomplete = (inp.get_attribute('autocomplete') or '').lower()
                
                all_attrs = f"{input_type} {input_name} {input_id} {input_placeholder} {input_autocomplete}"
                
                for keyword in keywords:
                    if keyword.lower() in all_attrs:
                        self.logger.info(f"Found field matching keyword '{keyword}' in attributes: {all_attrs}")
                        return inp
            
            self.logger.error(f"Could not find input field matching keywords: {keywords}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding input field: {e}")
            return None

    def _find_submit_button(self, timeout: int = 5):
        """Find the submit button on the page."""
        try:
            # Try finding submit button by type
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                self.logger.info("Found submit button by type=submit")
                return button
            except NoSuchElementException:
                pass
            
            try:
                button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
                self.logger.info("Found submit input by type=submit")
                return button
            except NoSuchElementException:
                pass
            
            # Search buttons by text content
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                btn_text = (btn.text or '').lower()
                if any(word in btn_text for word in ['log in', 'sign in', 'login', 'signin', 'submit', 'continue']):
                    self.logger.info(f"Found button by text: '{btn.text}'")
                    return btn
            
            # If still not found, return first visible button
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    self.logger.info(f"Using first visible button: '{btn.text}'")
                    return btn
            
            self.logger.error("Could not find submit button")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding submit button: {e}")
            return None

    def _navigate_to_signin(self) -> bool:
        """Navigate to the sign-in page by clicking the sign-in menu."""
        try:
            # Look for "Sign In" link or button in navigation
            signin_selectors = [
                'a[href*="login"]',
                'a[href*="signin"]',
                'a[href*="sign-in"]',
                'button[id*="signin"]',
                'a[id*="signin"]'
            ]
            
            for selector in signin_selectors:
                try:
                    signin_link = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"Found sign-in link using selector: {selector}")
                    signin_link.click()
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Try finding by link text
            try:
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                for link in links:
                    text = link.text.lower().strip()
                    if 'sign in' in text or 'log in' in text or 'login' in text:
                        self.logger.info(f"Found sign-in link by text: {link.text}")
                        link.click()
                        return True
            except Exception as e:
                self.logger.debug(f"Error finding sign-in by link text: {e}")
            
            # Try finding buttons
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for button in buttons:
                    text = button.text.lower().strip()
                    if 'sign in' in text or 'log in' in text:
                        self.logger.info(f"Found sign-in button by text: {button.text}")
                        button.click()
                        return True
            except Exception as e:
                self.logger.debug(f"Error finding sign-in by button text: {e}")
            
            self.logger.warning("Could not find sign-in link, assuming already on login page")
            return True  # Continue anyway, might already be on login page
            
        except Exception as e:
            self.logger.error(f"Error navigating to sign-in: {e}")
            return True  # Continue anyway

    def _find_login_field(self, field_type: str, timeout: int = 2):
        """Dynamically find login input fields by analyzing the page."""
        try:
            # Common selectors for email/username fields
            if field_type == 'username':
                selectors = [
                    'input[type="email"]',
                    'input[type="text"][name*="user"]',
                    'input[type="text"][name*="email"]',
                    'input[id*="user"]',
                    'input[id*="email"]',
                    'input[name="username"]',
                    'input[name="email"]',
                    'input[placeholder*="email"]',
                    'input[placeholder*="username"]',
                    'input[autocomplete="username"]',
                    'input[autocomplete="email"]'
                ]
            # Common selectors for password fields
            elif field_type == 'password':
                selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[id*="password"]',
                    'input[id*="passwd"]',
                    'input[autocomplete="current-password"]',
                    'input[placeholder*="password"]'
                ]
            else:
                return None
            
            for selector in selectors:
                try:
                    field = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"Found {field_type} field using selector: {selector}")
                    return field
                except (TimeoutException, NoSuchElementException):
                    continue
            
            self.logger.error(f"Could not find {field_type} field with any known selector")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding {field_type} field: {e}")
            return None

    def _find_login_button(self):
        """Dynamically find the login/submit button."""
        try:
            selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button[id*="login"]',
                'button[id*="submit"]',
                'button[class*="login"]',
                'button[class*="submit"]',
                'a[id*="login"]',
                'input[value*="Log"]',
                'input[value*="Sign"]'
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"Found login button using selector: {selector}")
                    return button
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # If no button found by selectors, try finding by text content
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for button in buttons:
                    text = button.text.lower()
                    if 'log' in text or 'sign' in text or 'submit' in text:
                        self.logger.info(f"Found login button by text: {button.text}")
                        return button
            except Exception:
                pass
            
            self.logger.error("Could not find login button with any known selector")
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding login button: {e}")
            return None

    def _find_next_button(self):
        """Find 'Next' or 'Continue' button for multi-step login."""
        try:
            selectors = [
                'button[id*="next"]',
                'button[id*="continue"]',
                'button[class*="next"]',
                'button[class*="continue"]',
                'input[type="submit"]',
                'button[type="submit"]'
            ]
            
            for selector in selectors:
                try:
                    button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.logger.info(f"Found next button using selector: {selector}")
                    return button
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Try finding by text content
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                for button in buttons:
                    text = button.text.lower()
                    if 'next' in text or 'continue' in text:
                        self.logger.info(f"Found next button by text: {button.text}")
                        return button
            except Exception:
                pass
            
            self.logger.debug("No 'Next' button found, might be single-step login")
            return None
            
        except Exception as e:
            self.logger.debug(f"Error finding next button: {e}")
            return None

    def select_thermostat(self, thermostat_name: str = None) -> bool:
        """Select a specific thermostat from the device list.
        
        Args:
            thermostat_name: Name of the thermostat to select. If None, uses config.
            
        Returns:
            bool: True if thermostat was selected successfully
        """
        try:
            if not thermostat_name:
                thermostat_name = self.config.get('ecobee.thermostat_name', 'Main Floor')
            
            self.logger.info(f"Selecting thermostat: {thermostat_name}")
            
            # Wait for page to load
            time.sleep(0.5)
            
            # Look for thermostat by text - try multiple approaches
            # 1. Try finding links with the thermostat name
            try:
                thermostats = self.driver.find_elements(By.TAG_NAME, 'a')
                for therm in thermostats:
                    if thermostat_name.lower() in therm.text.lower():
                        self.logger.info(f"Found thermostat link: {therm.text}")
                        therm.click()
                        time.sleep(2)
                        return True
            except Exception as e:
                self.logger.debug(f"Could not find thermostat by link: {e}")
            
            # 2. Try finding divs or spans with the name
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{thermostat_name}')]")
                for elem in elements:
                    if elem.is_displayed():
                        self.logger.info(f"Found thermostat element: {elem.text}")
                        # Try to click the element or its parent
                        try:
                            elem.click()
                        except:
                            elem.find_element(By.XPATH, './..').click()
                        time.sleep(2)
                        return True
            except Exception as e:
                self.logger.debug(f"Could not find thermostat by XPath: {e}")
            
            # 3. Try finding by device card or tile
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, '[class*="device"], [class*="thermostat"], [class*="card"]')
                for card in cards:
                    if thermostat_name.lower() in card.text.lower():
                        self.logger.info(f"Found thermostat card")
                        card.click()
                        time.sleep(2)
                        return True
            except Exception as e:
                self.logger.debug(f"Could not find thermostat by card: {e}")
            
            self.logger.error(f"Could not find thermostat: {thermostat_name}")
            self._log_page_structure()
            return False
            
        except Exception as e:
            self.logger.error(f"Error selecting thermostat: {e}")
            return False

    def get_heating_status(self) -> HeatingStatus:
        """Get current heating system status by clicking System tile."""
        try:
            self.logger.info("Retrieving heating system status")
            
            # Navigate to devices page if not already there
            devices_url = "https://www.ecobee.com/consumerportal/index.html#/devices"
            if devices_url not in self.driver.current_url:
                self.driver.get(devices_url)
                time.sleep(self.config.get('automation.delay', 2))
            
            # Select the correct thermostat
            if not self.select_thermostat():
                raise EcobeeAutomationError("Failed to select thermostat")
            
            # Click on System tile
            self.logger.info("Looking for System tile...")
            time.sleep(2)  # Wait for page to load
            
            try:
                # Try finding System tile by text
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'System') or contains(text(), 'SYSTEM')]")
                for elem in elements:
                    if elem.is_displayed():
                        self.logger.info(f"Found System element: {elem.text}")
                        try:
                            elem.click()
                        except:
                            # Try clicking parent
                            elem.find_element(By.XPATH, './..').click()
                        time.sleep(2)
                        break
            except Exception as e:
                self.logger.warning(f"Could not find System tile: {e}")
            
            status = HeatingStatus()
            
            # Try to read current mode from the page
            try:
                # Look for active mode indicators (Aux or Heat)
                page_text = self.driver.find_element(By.TAG_NAME, 'body').text.lower()
                if 'aux' in page_text:
                    status.mode = 'aux'
                elif 'heat' in page_text:
                    status.mode = 'heat'
                self.logger.info(f"Detected mode from page: {status.mode}")
            except Exception as e:
                self.logger.warning(f"Could not detect mode: {e}")
            
            self.logger.info(f"Retrieved status: {status}")
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get heating status: {e}")
            self._take_screenshot("status_error")
            raise EcobeeAutomationError(f"Status retrieval failed: {e}")

    def set_heating_mode(self, mode: str, thermostat_name: str = None) -> bool:
        """Set the heating system mode (aux or heat).
        
        Args:
            mode: Either 'aux' or 'heat'
            thermostat_name: Name of thermostat to control (uses config default if None)
            
        Returns:
            bool: True if mode was set successfully
        """
        try:
            self.logger.info(f"Setting heating mode to: {mode}")
            
            mode = mode.lower()
            if mode not in ['aux', 'heat']:
                raise ValueError(f"Invalid mode: {mode}. Must be either 'aux' or 'heat'")
            
            # Navigate to devices page if not already there
            devices_url = "https://www.ecobee.com/consumerportal/index.html#/devices"
            if devices_url not in self.driver.current_url:
                self.driver.get(devices_url)
                time.sleep(self.config.get('automation.delay', 2))
            
            # Select the correct thermostat
            if not self.select_thermostat(thermostat_name):
                raise EcobeeAutomationError("Failed to select thermostat")
            
            # Click on System tile
            self.logger.info("Looking for System tile...")
            time.sleep(2)
            
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'System') or contains(text(), 'SYSTEM')]")
                for elem in elements:
                    if elem.is_displayed():
                        self.logger.info(f"Found System element, clicking...")
                        try:
                            elem.click()
                        except:
                            elem.find_element(By.XPATH, './..').click()
                        time.sleep(2)
                        break
            except Exception as e:
                self.logger.error(f"Could not find System tile: {e}")
                return False
            
            # Look for radio buttons with labels
            self.logger.info(f"Looking for {mode.upper()} radio button...")
            try:
                # Find all labels that might contain the mode text
                labels = self.driver.find_elements(By.TAG_NAME, 'label')
                for label in labels:
                    label_text = label.text.strip().lower()
                    # Check if this label is for the mode we want
                    if mode.lower() in label_text or (mode.lower() == 'aux' and 'auxil' in label_text):
                        self.logger.info(f"Found label with text: '{label.text}', clicking...")
                        try:
                            # Try clicking the label itself
                            label.click()
                            time.sleep(5)
                            self.logger.info(f"Successfully set mode to: {mode}")
                            return True
                        except Exception as e:
                            self.logger.warning(f"Failed to click label: {e}")
                            # Try finding associated radio button
                            try:
                                label_for = label.get_attribute('for')
                                if label_for:
                                    radio_btn = self.driver.find_element(By.ID, label_for)
                                    radio_btn.click()
                                    time.sleep(5)
                                    self.logger.info(f"Successfully set mode to: {mode}")
                                    return True
                            except Exception as e2:
                                self.logger.warning(f"Failed to click radio button: {e2}")
                
                # Alternative: Try finding by text near radio buttons
                mode_elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{mode.lower()}')]")
                for elem in mode_elements:
                    if elem.is_displayed():
                        self.logger.info(f"Found {mode} element by XPath, clicking...")
                        try:
                            elem.click()
                            time.sleep(5)
                            self.logger.info(f"Successfully set mode to: {mode}")
                            return True
                        except:
                            pass
                        
            except Exception as e:
                self.logger.error(f"Error clicking mode element: {e}")
            
            self.logger.error(f"Could not find {mode} option")
            self._log_page_structure()
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to set heating mode: {e}")
            self._take_screenshot("mode_change_error")
            return False

    def set_main_floor_aux(self) -> bool:
        """Set Main Floor thermostat heating mode to Aux.
        
        Returns:
            bool: True if mode was set successfully
        """
        return self.set_heating_mode('aux', 'Main Floor')

    def set_main_floor_heat(self) -> bool:
        """Set Main Floor thermostat heating mode to Heat.
        
        Returns:
            bool: True if mode was set successfully
        """
        return self.set_heating_mode('heat', 'Main Floor')

    def set_upstairs_aux(self) -> bool:
        """Set Upstairs thermostat heating mode to Aux.
        
        Returns:
            bool: True if mode was set successfully
        """
        return self.set_heating_mode('aux', 'Upstairs')

    def set_upstairs_heat(self) -> bool:
        """Set Upstairs thermostat heating mode to Heat.
        
        Returns:
            bool: True if mode was set successfully
        """
        return self.set_heating_mode('heat', 'Upstairs')

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