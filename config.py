import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

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
    EXCEL_FILE = os.getenv("EXCEL_FILE", "table_main_2568.xlsx")
    
    # Browser Settings
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1920,1080")
    
    # Logging
    LOG_FILE = "cen_automation.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Ensure critical environment variables are set."""
        missing = []
        if not cls.USERNAME: missing.append("CEN_USERNAME")
        if not cls.PASSWORD: missing.append("CEN_PASSWORD")
        
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")
