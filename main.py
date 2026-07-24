import os
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.config import Config
from core.utils import setup_logger, setup_driver, get_table_df, handle_pagination

# Initialize Logger
logger = setup_logger()

def login(driver, wait):
    """Log in and navigate to the tracking system."""
    logger.info(f"Navigating to login: {Config.LOGIN_URL}")
    driver.get(Config.LOGIN_URL)
    
    try:
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "Username")))
        pass_field = driver.find_element(By.NAME, "Password")
        login_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-primary[type='submit']")
        
        user_field.send_keys(Config.USERNAME)
        pass_field.send_keys(Config.PASSWORD)
        login_btn.click()
        logger.info("Logged in successfully.")
        
        # Go to tracking system
        tracking_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[./img[@alt='banner-track']]")))
        tracking_link.click()
        
        # Wait for loading overlay to disappear
        loading_overlay = (By.XPATH, "//div[contains(@style, 'z-index: 9999')]")
        wait.until(EC.invisibility_of_element_located(loading_overlay))
        logger.info("Tracking Dashboard ready.")
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise

def get_column_indices(df):
    """Dynamically find column indices based on headers."""
    headers = df.columns.tolist()
    indices = {
        'name': next((i for i, h in enumerate(headers) if 'ชื่อ' in str(h)), 1),
        'percent': next((i for i, h in enumerate(headers) if '%' in str(h) or 'เบิกจ่าย' in str(h)), 8)
    }
    return indices

def process_page_items(driver, wait, main_excel_df):
    """Process all items in the current table view with stable navigation."""
    df_current = get_table_df(driver)
    if df_current.empty:
        return

    col_map = get_column_indices(df_current)
    logger.debug(f"Column mapping: {col_map}")

    try:
        for idx, row in df_current.iterrows():
            # Parse percentage
            raw_percent = str(row.iloc[col_map['percent']]).replace(',', '')
            try:
                percent_val = float(raw_percent)
            except ValueError:
                continue

            # Criteria: % disbursement < 100
            if percent_val < 100:
                item_name = str(row.iloc[col_map['name']]).strip()
                logger.info(f"Processing: {item_name} ({percent_val}%)")
                
                # Check if item exists in our tracking Excel
                # (Optional: refine matching logic)
                matched = main_excel_df[main_excel_df['ชื่อ / ประมาณการ'].str.contains(item_name, na=False, regex=False)]
                
                if not matched.empty:
                    try:
                        # Find the button in this specific row
                        # normalize-space() helps with whitespace issues in HTML
                        btn_xpath = f"//tbody/tr[td[normalize-space()='{item_name}']]//div[@data-tip='เรียกดูข้อมูลแถบเดิม']/button"
                        action_btn = driver.find_element(By.XPATH, btn_xpath)
                        
                        # STABLE NAVIGATION: Open in new tab using Ctrl+Click or JavaScript
                        main_window = driver.current_window_handle
                        driver.execute_script("window.open(arguments[0].getAttribute('onclick') || '', '_blank');", action_btn)
                        
                        # Wait for new tab and switch
                        wait.until(lambda d: len(d.window_handles) > 1)
                        new_window = [h for h in driver.window_handles if h != main_window][0]
                        driver.switch_to.window(new_window)
                        
                        # --- WORK IN DETAIL PAGE ---
                        logger.info(f"  In detail page for: {item_name}")
                        # Example: wait.until(EC.presence_of_element_located((By.XPATH, "//table")))
                        time.sleep(1) # Brief pause for visual confirmation if not headless
                        
                        # Close tab and return
                        driver.close()
                        driver.switch_to.window(main_window)
                        
                    except Exception as sub_e:
                        logger.error(f"  Error processing {item_name}: {sub_e}")
                        # Ensure we are back on the main window if something failed
                        if len(driver.window_handles) > 1:
                            driver.close()
                        driver.switch_to.window(main_window)
    except Exception as e:
        logger.error(f"Processing loop error: {e}")

def main(budget_year: str = None, excel_file: str = None):
    # Validate configuration
    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(e)
        return

    target_year = budget_year or Config.BUDGET_YEAR
    target_excel = excel_file or Config.EXCEL_FILE

    if not os.path.exists(target_excel):
        logger.error(f"Excel file not found: {target_excel}")
        return

    logger.info(f"Starting automation for Year: {target_year} using Excel: {target_excel}...")
    main_excel_df = pd.read_excel(target_excel)
    driver = setup_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        login(driver, wait)
        
        # Navigate to target page
        target_url = f"{Config.TRACKING_URL}?BudgetYear={target_year}&BudgetSourceID=1"
        logger.info(f"Jumping to Budget Page: {target_url}")
        driver.get(target_url)
        
        page = 1
        while True:
            logger.info(f"Processing Page {page}...")
            process_page_items(driver, wait, main_excel_df)
            
            if not handle_pagination(driver, wait):
                logger.info("Pagination finished.")
                break
            page += 1
            
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
    finally:
        logger.info("Closing browser.")
        driver.quit()

if __name__ == "__main__":
    main()
