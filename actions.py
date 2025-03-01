#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime, timedelta

# Define base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define directories
files_dir = os.path.join(BASE_DIR, "files")
json_dir = os.path.join(BASE_DIR, "telegram_data")
xlsx_dir = os.path.join(BASE_DIR, "analyzed_tables")
log_file = os.path.join(files_dir, "script.log")

# Ensure directories exist
os.makedirs(files_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)
os.makedirs(xlsx_dir, exist_ok=True)

# Define cutoff date (3 days old)
cutoff_date = datetime.now() - timedelta(days=3)

# Get today's date (D-M-Y) for checking JSON files
today_date = datetime.now().strftime("%d-%m-%Y")

def log(message):
    """Write logs to both console and a file."""
    formatted_message = f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] {message}"
    print(formatted_message)
    try:
        with open(log_file, "a", encoding="utf-8") as log_f:
            log_f.write(formatted_message + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")

def delete_old_files(directory):
    """Delete files older than 3 days."""
    if not os.path.exists(directory):
        log(f"Directory not found: {directory}")
        return
    try:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    log(f"Deleting {file_path}")
                    os.remove(file_path)
    except Exception as e:
        log(f"Error deleting files in {directory}: {e}")

def run_script(script_name):
    """Run a Python script inside the virtual environment and wait for it to complete."""
    log(f"Starting script: {script_name}")
    script_path = os.path.join(BASE_DIR, script_name)
    try:
        result = subprocess.run(
            [f"{BASE_DIR}/venv/bin/python3", script_path],  # Runs inside venv
            check=True,
            capture_output=True,
            text=True
        )
        log(f"Finished script: {script_name}")
        log(f"Output:\n{result.stdout}")
        if result.stderr:
            log(f"Errors:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        log(f"Error running {script_name}: {e}")
        log(f"Script Output:\n{e.output}")
        log(f"Script Error Output:\n{e.stderr}")

def json_file_exists():
    """Check if a JSON file from today exists in the telegram_data directory."""
    try:
        for file in os.listdir(json_dir):
            if file.endswith(".json") and today_date in file:
                return True
    except Exception as e:
        log(f"Error checking JSON files: {e}")
    return False

def main():
    log("Running cleanup process...")
    delete_old_files(json_dir)
    delete_old_files(xlsx_dir)

    keywords_file = "/opt/python_projects/telegram_shopping/files/keywords.txt"

    if not os.path.exists(keywords_file):
        log(f"ERROR: Missing keywords.txt . Stopping execution.")
        return
    else:
        log(f"SUCCESS: Found keywords.txt")


    try:
        # Run main.py only if keywords.txt exists
        run_script("main.py")

        # Check if today's JSON file exists before running the next scripts
        if not json_file_exists():
            log("No JSON file from today found. Stopping execution.")
            return

        # Run remaining scripts sequentially
        run_script("generate_summary.py")
        run_script("gpt_api.py")

        log("All tasks completed.")
    except Exception as e:
        log(f"Critical error in main execution: {e}")

if __name__ == "__main__":
    main()


