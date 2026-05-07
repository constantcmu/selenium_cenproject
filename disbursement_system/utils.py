import logging
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
    chrome_options = Options()
    if Config.HEADLESS:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={Config.WINDOW_SIZE}")
    
    # Speed optimization
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fast_login(driver, wait):
    logger.info(f"Navigating to: {Config.LOGIN_URL}")
    driver.get(Config.LOGIN_URL)
    
    try:
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "Username")))
        pass_field = driver.find_element(By.NAME, "Password")
        login_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-primary[type='submit']")
        
        user_field.send_keys(Config.USERNAME)
        pass_field.send_keys(Config.PASSWORD)
        login_btn.click()
        logger.info("Login successful.")
        
        # Banner check
        tracking_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[./img[@alt='banner-track']]")))
        tracking_link.click()
        
        loading_overlay = (By.XPATH, "//div[contains(@style, 'z-index: 9999')]")
        wait.until(EC.invisibility_of_element_located(loading_overlay))
        logger.info("Dashboard is ready.")
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise


def fast_navigate_to_target_url(driver, wait):
    try:
        logger.info(f"Navigating to Target URL: {Config.TARGET_URL}")
        driver.get(Config.TARGET_URL)
        loading_overlay = (By.XPATH, "//div[contains(@style, 'z-index: 9999')]")
        wait.until(EC.invisibility_of_element_located(loading_overlay))
        logger.info("Navigate to Target URL successfully.")
    except TimeoutException:
        logger.error("!!! Timeout waiting for Target URL to load or overlay to disappear.")
        raise
    except Exception as e:
        logger.error(f"Navigate to Target URL error: {e}")
        raise


def fill_disbursement_form(driver, wait, data):
    """
    Logic for filling the 'Add Disbursement' modal.
    data: dict containing gfmis_code, date, amount_contract, amount_self
    """
    try:
        logger.info(f"Filling form for GFMIS: {data['gfmis_code']}")
        
        # 1. Click 'เพิ่มข้อมูล' button
        try:
            btn_add = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'เพิ่มข้อมูล')]")))
            btn_add.click()
        except TimeoutException:
            logger.error("!!! ไม่พบปุ่ม 'เพิ่มข้อมูล' (คุณอาจจะยังไม่ได้เข้าไปในหน้าละเอียดของโครงการ)")
            return False
        
        # 2. Fill GFMIS Code
        try:
            gfmis_field = wait.until(EC.presence_of_element_located((By.NAME, "GFMISCode")))
            gfmis_field.clear()
            gfmis_field.send_keys(data['gfmis_code'])
        except TimeoutException:
            logger.error("!!! ไม่พบช่องกรอก 'รหัส GFMIS' ในหน้าต่าง Pop-up")
            return False
        
        # 3. Fill Date (Use JS for readonly field)
        date_field = driver.find_element(By.NAME, "RegisterDate")
        driver.execute_script("arguments[0].value = arguments[1];", date_field, data['date'])
        
        # 4. Fill Amounts
        vendor_field = driver.find_element(By.NAME, "SumVendorUsedBudgetResult")
        vendor_field.clear()
        vendor_field.send_keys(str(data['amount_contract']))
        
        self_field = driver.find_element(By.NAME, "SumSelfUsedBudgetResult")
        self_field.clear()
        self_field.send_keys(str(data['amount_self']))
        
        # 5. Click Save
        save_btn = driver.find_element(By.XPATH, "//button[text()='บันทึก']")
        
        # --- [ระวัง: บรรทัดด้านล่างคือการกดบันทึกจริง] ---
        # save_btn.click() 
        
        logger.info("Form filled successfully.")
        return True
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
