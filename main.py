import requests
from fastapi import FastAPI, HTTPException
import os
from functions import *
import subprocess
from dotenv import load_dotenv

load_dotenv()
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise RuntimeError("AIPROXY_TOKEN is missing! Set it in .env or environment variables.")
app = FastAPI()
### /run and /read
@app.get("/read")
async def read_file(path: str):
        if not path.startswith("/data"):
             raise HTTPException(status_code = 403, detail = "Access to file is not allowed")
        if not os.path.exists(path):
             raise HTTPException(status_code = 404 , detail = "File is not found")
        with open(path, "r", encoding="utf-8") as file:
            return {"content": file.read()}
@app.post("/run")
async def run_task(task: str):
    try:
        task_output = get_task_output(AIPROXY_TOKEN, task)
        task = task.lower()
        if "install uv" in task or "run datagen" in task:
            return install_uv_and_run_datagen()
        elif "format" in task and "prettier" in task:
            return format_file_with_prettier()
        elif "count" in task:
            day = extract_dayname(task)
            return count_weekdays(day)
        elif "sort contacts" in task:
            return sort_contacts()
        elif "recent logs" in task:
            return extract_recent_logs()
        elif "markdown index" in task:
            return create_markdown_index()
        elif "email sender" in task:
            return extract_email_sender(AIPROXY_TOKEN)
        elif "credit card" in task:
            return extract_credit_card_number(AIPROXY_TOKEN)
        elif "similar comments" in task:
            return find_similar_comments(AIPROXY_TOKEN)
        elif "ticket sales" in task:
            return calculate_ticket_sales()
        elif "fetch data" in task:
            return fetch_data_from_api(task)
        elif "clone repo" in task:
            return clone_and_commit_repo(task)
        elif "run sql query" in task:
            return run_sql_query(task)
        elif "scrape website" in task:
            return scrape_website(task)
        elif "resize image" in task or "compress image" in task:
            return compress_or_resize_image(task)
        elif "transcribe audio" in task:
            return transcribe_audio()
        elif "convert markdown" in task:
            return convert_markdown_to_html()
        elif "filter csv" in task:
            return filter_csv(task)
        else:
            return {"status": "Task recognized but not implemented yet"}

        return {"status": "success", "task_output": task_output}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))