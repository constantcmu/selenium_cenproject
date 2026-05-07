import sys
import os
from selenium.webdriver.support.ui import WebDriverWait
from config import Config
from utils import setup_logger, setup_driver, fast_login, fill_disbursement_form

# Initialize
logger = setup_logger()

def main():
    try:
        Config.validate()
    except EnvironmentError as e:
        logger.error(e)
        return

    logger.info(f"--- Starting Disbursement System (Year: {Config.BUDGET_YEAR}) ---")
    
    driver = setup_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        # 1. Login
        fast_login(driver, wait)
        
        # 2. Example: Navigate to a specific project directly or via list
        # target_url = f"{Config.BASE_URL}/track/budget/XXX/YYY/budget-disburse?BudgetYear={Config.BUDGET_YEAR}"
        # logger.info(f"Navigating to target project: {target_url}")
        # driver.get(target_url)
        
        # 3. Example Data for filling (You can loop this from Excel)
        sample_data = {
            'gfmis_code': '07003540037003220226',
            'date': '01/08/2568',
            'amount_contract': 100000,
            'amount_self': 0
        }
        
        # 4. Fill the form (Test with one record)
        # result = fill_disbursement_form(driver, wait, sample_data)
        # if result:
        #     logger.info("Successfully processed disbursement record.")
            
        logger.info("System is ready for batch processing. Please configure your Excel loop in main.py")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")
    finally:
        logger.info("Shutting down driver.")
        driver.quit()

if __name__ == "__main__":
    main()
