import os
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Import main budget automation script
import main as budget_bot

# Set up logging for API itself
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CEN_API")

app = FastAPI(
    title="CEN Automation Project API",
    description="API for controlling Selenium automation bots for cenproject.rid.go.th",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, customize in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep track of active bot jobs (Simple in-memory state)
bot_state = {
    "budget_tracker": {
        "running": False,
        "last_run": None,
        "error": None
    },
    "disbursement_system": {
        "running": False,
        "last_run": None,
        "error": None
    }
}

class BudgetTrackerRequest(BaseModel):
    budget_year: Optional[str] = None
    excel_file: Optional[str] = None

# Background task runner for Budget Tracker
def run_budget_tracker_task(year: Optional[str], excel: Optional[str]):
    bot_state["budget_tracker"]["running"] = True
    bot_state["budget_tracker"]["error"] = None
    try:
        logger.info(f"Starting Budget Tracker. Year={year}, Excel={excel}")
        budget_bot.main(budget_year=year, excel_file=excel)
        logger.info("Budget Tracker finished successfully.")
    except Exception as e:
        logger.error(f"Error in Budget Tracker: {e}", exc_info=True)
        bot_state["budget_tracker"]["error"] = str(e)
    finally:
        bot_state["budget_tracker"]["running"] = False

# Background task runner for Disbursement System
def run_disbursement_task():
    bot_state["disbursement_system"]["running"] = True
    bot_state["disbursement_system"]["error"] = None
    try:
        logger.info("Starting Disbursement System...")
        import sys
        import subprocess
        cmd = [sys.executable, "main.py"]
        cwd = os.path.abspath("./disbursement_system")
        process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if process.returncode != 0:
            raise Exception(process.stderr or process.stdout)
        logger.info("Disbursement System finished successfully.")
    except Exception as e:
        logger.error(f"Error in Disbursement System: {e}", exc_info=True)
        bot_state["disbursement_system"]["error"] = str(e)
    finally:
        bot_state["disbursement_system"]["running"] = False

@app.get("/")
def get_root():
    return {
        "message": "CEN Project Automation API is running!",
        "endpoints": {
            "POST /api/run/budget-tracker": "Run budget scraper",
            "POST /api/run/disbursement": "Run disbursement automation form filler",
            "GET /api/status": "Check active jobs and logs"
        }
    }

@app.post("/api/run/budget-tracker")
def run_budget_tracker(payload: BudgetTrackerRequest, background_tasks: BackgroundTasks):
    if bot_state["budget_tracker"]["running"]:
        raise HTTPException(status_code=400, detail="Budget tracker is already running.")
        
    background_tasks.add_task(
        run_budget_tracker_task, 
        payload.budget_year, 
        payload.excel_file
    )
    return {
        "status": "started",
        "message": "Budget tracking automation initiated in the background."
    }

@app.post("/api/run/disbursement")
def run_disbursement(background_tasks: BackgroundTasks):
    if bot_state["disbursement_system"]["running"]:
        raise HTTPException(status_code=400, detail="Disbursement system is already running.")
        
    background_tasks.add_task(run_disbursement_task)
    return {
        "status": "started",
        "message": "Disbursement automation initiated in the background."
    }

@app.get("/api/status")
def get_status():
    # Read last 15 lines of log files for status dashboard
    logs = {"budget_tracker": "", "disbursement_system": ""}
    
    if os.path.exists("cen_automation.log"):
        with open("cen_automation.log", "r", encoding="utf-8") as f:
            logs["budget_tracker"] = "".join(f.readlines()[-15:])
            
    disburse_log_path = os.path.join("disbursement_system", "disbursement_automation.log")
    if os.path.exists(disburse_log_path):
        with open(disburse_log_path, "r", encoding="utf-8") as f:
            logs["disbursement_system"] = "".join(f.readlines()[-15:])
            
    return {
        "jobs": bot_state,
        "logs": logs
    }

# Mount static files folder to serve the web application dashboard
app.mount("/static", StaticFiles(directory="frontend"), name="static")

