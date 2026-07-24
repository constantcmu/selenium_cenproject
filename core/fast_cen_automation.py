import os
import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

# 1. Load configuration
load_dotenv()
USERNAME = os.getenv("CEN_USERNAME")
PASSWORD = os.getenv("CEN_PASSWORD")
LOGIN_URL = "https://cenproject.rid.go.th/"
BUDGET_YEAR = "2025"
EXCEL_FILE = "table_main_2568.xlsx"

def setup_driver():
    """Optimized Chrome configuration for speed."""
    chrome_options = Options()
    # Uncomment the line below to run without opening a browser window (Faster)
    # chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Disable images to save bandwidth and speed up loading
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fast_login(driver, wait):
    """Log in quickly and navigate to the tracking system."""
    print(f"[*] Navigating to login: {LOGIN_URL}")
    driver.get(LOGIN_URL)
    
    try:
        user_field = wait.until(EC.presence_of_element_located((By.NAME, "Username")))
        pass_field = driver.find_element(By.NAME, "Password")
        login_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-primary[type='submit']")
        
        user_field.send_keys(USERNAME)
        pass_field.send_keys(PASSWORD)
        login_btn.click()
        print("[+] Logged in successfully")
        
        # Go to tracking system
        tracking_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[./img[@alt='banner-track']]")))
        tracking_link.click()
        
        # Wait for loading overlay to disappear
        loading_overlay = (By.XPATH, "//div[contains(@style, 'z-index: 9999')]")
        wait.until(EC.invisibility_of_element_located(loading_overlay))
        print("[+] Tracking Dashboard ready")
        
    except Exception as e:
        print(f"[!] Login error: {e}")
        driver.quit()
        raise

def get_table_df(driver):
    """Extract table data into a Pandas DataFrame instantly using BeautifulSoup."""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'class': 'table-zebra'})
        if not table:
            return pd.DataFrame()
        
        # Use pandas to parse the HTML table
        df = pd.read_html(str(table))[0]
        return df
    except Exception as e:
        print(f"[!] Error parsing table: {e}")
        return pd.DataFrame()

def handle_pagination(driver, wait):
    """Navigate to the next page if available."""
    try:
        # Check if there is a next page based on text like "แสดงข้อมูล X ถึง Y จาก Z"
        pagination_div = driver.find_element(By.XPATH, "//div[contains(text(), 'แสดงข้อมูล')]")
        numbers = re.findall(r'\d+', pagination_div.text)
        
        if len(numbers) >= 3:
            current_last = int(numbers[1])
            total = int(numbers[2])
            if current_last < total:
                next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.mx-4 + button")))
                if next_btn.is_enabled():
                    print("[*] Moving to next page...")
                    driver.execute_script("arguments[0].click();", next_btn)
                    # Wait for table to update (stale check)
                    wait.until(EC.staleness_of(pagination_div))
                    return True
        return False
    except (NoSuchElementException, TimeoutException):
        return False

def process_page_items(driver, wait, main_excel_df):
    """Process all items in the current table view."""
    df_current = get_table_df(driver)
    if df_current.empty:
        return

    # Filter rows that need attention (e.g., % disbursement < 100)
    # Adjust column index (9th column usually has %)
    try:
        for idx, row in df_current.iterrows():
            # Basic parsing of the percentage column
            raw_percent = str(row.iloc[8]).replace(',', '')
            try:
                percent_val = float(raw_percent)
            except ValueError:
                continue

            if percent_val < 100:
                item_name = str(row.iloc[1]).strip()
                print(f"  [!] Found: {item_name} ({percent_val}%)")
                
                # Verify against Excel if needed
                matched = main_excel_df[main_excel_df['ชื่อ / ประมาณการ'] == item_name]
                if not matched.empty:
                    # Logic to click and process the specific item
                    # We use a targeted XPath for the button in this specific row
                    try:
                        btn_xpath = f"//tbody/tr[td[2][normalize-space()='{item_name}']]//div[@data-tip='เรียกดูข้อมูลแถบเดิม']/button"
                        action_btn = driver.find_element(By.XPATH, btn_xpath)
                        driver.execute_script("arguments[0].click();", action_btn)
                        
                        # -- DO WORK IN SUB-PAGE HERE --
                        wait.until(EC.presence_of_element_located((By.XPATH, "//table"))) 
                        print(f"    [+] Processed detail for: {item_name}")
                        
                        driver.back()
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-zebra")))
                    except Exception as sub_e:
                        print(f"    [?] Failed to click {item_name}: {sub_e}")
    except Exception as e:
        print(f"[!] Processing error: {e}")

def main():
    if not os.path.exists(EXCEL_FILE):
        print(f"[!] Error: {EXCEL_FILE} not found.")
        return

    main_excel_df = pd.read_excel(EXCEL_FILE)
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        fast_login(driver, wait)
        
        # Direct navigation to the Budget 2568 page
        target_url = f"https://cenproject.rid.go.th/track/budget?BudgetYear={BUDGET_YEAR}&BudgetSourceID=1"
        print(f"[*] Jumping to Budget Page: {target_url}")
        driver.get(target_url)
        
        page = 1
        while True:
            print(f"[*] Processing Page {page}")
            process_page_items(driver, wait, main_excel_df)
            
            if not handle_pagination(driver, wait):
                print("[*] Reached last page.")
                break
            page += 1
            
    except Exception as e:
        print(f"[!] Fatal error: {e}")
    finally:
        print("[*] Closing browser.")
        driver.quit()

if __name__ == "__main__":
    main()
