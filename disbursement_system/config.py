import os
from dotenv import load_dotenv
from pathlib import Path

# Look for .env in the current folder, then in the parent folder
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
    # Target for Budget Tracking
    BUDGET_TRACK_URL = f"{BASE_URL}/track/budget"
    
    # Application Constants
    # Default to 2026 (Year 2569) if not specified
    BUDGET_YEAR = os.getenv("BUDGET_YEAR", "2026")
    EXCEL_FILE = os.getenv("EXCEL_FILE", "table_main_2569.xlsx")
    
    # Browser Settings
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1920,1080")
    
    # Logging
    LOG_FILE = "disbursement_automation.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Ensure critical environment variables are set."""
        missing = []
        if not cls.USERNAME: missing.append("CEN_USERNAME")
        if not cls.PASSWORD: missing.append("CEN_PASSWORD")
        
        if missing:
            raise EnvironmentError(f"Missing required environment variables in .env: {', '.join(missing)}")
