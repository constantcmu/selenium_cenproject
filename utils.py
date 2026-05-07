import logging
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

def setup_logger():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=Config.LOG_LEVEL,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

def setup_driver():
    """Optimized Chrome configuration."""
    chrome_options = Options()
    if Config.HEADLESS:
        chrome_options.add_argument("--headless=new")
    
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={Config.WINDOW_SIZE}")
    
    # Disable images to save bandwidth
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_table_df(driver):
    """Extract table data using BeautifulSoup for speed."""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'class': 'table-zebra'})
        if not table:
            return pd.DataFrame()
        
        df = pd.read_html(str(table))[0]
        return df
    except Exception as e:
        logger.error(f"Error parsing table: {e}")
        return pd.DataFrame()

def handle_pagination(driver, wait):
    """
    Robust pagination handler.
    Checks if there's a next page and clicks the button.
    """
    try:
        # 1. Check pagination text (e.g., "แสดงข้อมูล 1 - 10 จาก 13 รายการ")
        pagination_text_xpath = "//div[contains(text(), 'แสดงข้อมูล')]"
        try:
            pagination_text_element = driver.find_element(By.XPATH, pagination_text_xpath)
            pagination_text = pagination_text_element.text
            
            numbers = re.findall(r'\d+', pagination_text)
            if len(numbers) >= 3:
                current_end = int(numbers[1])
                total_items = int(numbers[2])
                
                if current_end >= total_items:
                    logger.info("Reached last page.")
                    return False
        except NoSuchElementException:
            logger.warning("Pagination text not found.")
            return False

        # 2. Find and click Next button
        # Try different selectors for the Next button
        next_selectors = [
            (By.XPATH, "//button[contains(text(), '>')]"),
            (By.CSS_SELECTOR, "span.mx-4 + button"),
            (By.CSS_SELECTOR, "button[class*='btn']:last-child")
        ]
        
        next_button = None
        for selector_type, selector_val in next_selectors:
            try:
                btn = driver.find_element(selector_type, selector_val)
                if btn.is_enabled():
                    next_button = btn
                    break
            except NoSuchElementException:
                continue
        
        if next_button:
            # Scroll into view and click
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(0.5)
            
            # ActionChains click is more reliable for some UI frameworks
            ActionChains(driver).move_to_element(next_button).click().perform()
            
            # Wait for content to refresh (by checking for staleness of pagination text)
            wait.until(EC.staleness_of(pagination_text_element))
            # Briefly wait for the new table to be present
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-zebra")))
            
            return True
        else:
            logger.info("Next button not found or disabled.")
            return False

    except Exception as e:
        logger.error(f"Pagination error: {e}")
        return False
