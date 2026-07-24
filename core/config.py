import os
from dotenv import load_dotenv

from pathlib import Path

# Look for .env in current directory or parent directory
env_path = Path('.') / '.env'
if not env_path.exists():
    env_path = Path('..') / '.env'

load_dotenv(dotenv_path=env_path)

class Config:
    # Authentication
    USERNAME = os.getenv("CEN_USERNAME")
    PASSWORD = os.getenv("CEN_PASSWORD")
    
    # URLs
    BASE_URL = "https://cenproject.rid.go.th"
    LOGIN_URL = f"{BASE_URL}/"
    TRACKING_URL = f"{BASE_URL}/track/budget"
    
    # Application Constants
    BUDGET_YEAR = os.getenv("BUDGET_YEAR", "2025")
    
    # Default Excel file path (checks data/ folder first)
    _default_excel = os.getenv("EXCEL_FILE", "table_main_2568.xlsx")
    if os.path.exists(os.path.join("data", _default_excel)):
        EXCEL_FILE = os.path.join("data", _default_excel)
    else:
        EXCEL_FILE = _default_excel
    
    # Browser Settings
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1920,1080")
    
    # Logging
    LOG_FILE = os.path.join("data", "outputs", "cen_automation.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Ensure critical environment variables are set."""
        missing = []
        if not cls.USERNAME: missing.append("CEN_USERNAME")
        if not cls.PASSWORD: missing.append("CEN_PASSWORD")
        
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
