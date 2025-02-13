import os
import json
import requests
import subprocess
import sqlite3
import duckdb
import markdown
import re
from datetime import datetime
from fuzzywuzzy import fuzz
from PIL import Image
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

DATA_DIR = "/data"

if not AIPROXY_TOKEN:
    raise RuntimeError("AIPROXY_TOKEN is missing! Set it in .env or environment variables.")

### ✅ Helper Functions ###
def get_task_output(AIPROXY_TOKEN, task):
    """Send task to AIProxy and get a structured response."""
    client = OpenAI(api_key=AIPROXY_TOKEN)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": task}]
    )
    return response.choices[0].message.content.strip()

def is_safe_path(file_path):
    """Ensure access is restricted to /data directory."""
    abs_path = os.path.abspath(os.path.join(DATA_DIR, file_path))
    return abs_path.startswith(os.path.abspath(DATA_DIR))

### ✅ Operations Tasks (Phase A) ###

def count_weekdays(weekday):
    """Count the occurrences of a given weekday in /data/dates.txt."""
    try:
        file_path = os.path.join(DATA_DIR, "dates.txt")
        output_path = os.path.join(DATA_DIR, f"dates-{weekday.lower()}.txt")
        count = 0

        with open(file_path, "r") as f:
            for line in f:
                dt = datetime.strptime(line.strip(), "%Y-%m-%d")
                if dt.strftime("%A").lower() == weekday.lower():
                    count += 1

        with open(output_path, "w") as f:
            f.write(str(count))

        return {"message": f"Count of {weekday} written to {output_path}"}
    except Exception as e:
        return {"error": str(e)}, 500

def install_uv_and_run_datagen():
    """Install uv if required and run datagen.py."""
    try:
        subprocess.run(["uv", "--version"], check=True)
    except FileNotFoundError:
        subprocess.run(["pip", "install", "uv"], check=True)

    subprocess.run(
        ["uv", "run", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"],
        check=True, cwd=DATA_DIR
    )
    return {"message": "datagen.py executed successfully"}

def format_file_with_prettier():
    """Format /data/format.md using prettier."""
    try:
        subprocess.run(["npx", "prettier@3.4.2", "--write", f"{DATA_DIR}/format.md"], check=True)
        return {"message": "File formatted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

def extract_email_sender():
    """Extract sender’s email address from /data/email.txt using AIProxy."""
    try:
        input_file = os.path.join(DATA_DIR, "email.txt")
        output_file = os.path.join(DATA_DIR, "email-sender.txt")

        with open(input_file, "r", encoding="utf-8") as f:
            email_content = f.read()

        prompt = "Extract the sender's email address from this email and return only the email address."
        extracted_email = get_task_output(AIPROXY_TOKEN, f"{prompt}\n\n{email_content}")

        if "@" not in extracted_email:
            return {"error": "Invalid email extracted"}, 500

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_email)

        return {"message": "Email sender extracted and written to email-sender.txt"}
    except Exception as e:
        return {"error": str(e)}, 500

def extract_credit_card_number():
    """Extract credit card number from /data/credit_card.png using AIProxy."""
    try:
        input_file = os.path.join(DATA_DIR, "credit_card.png")
        output_file = os.path.join(DATA_DIR, "credit-card.txt")

        with open(input_file, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
            image_data_url = f"data:image/png;base64,{image_base64}"

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract the largest numeric sequence from this image. Return only the digits."},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]}
            ]
        }

        response = requests.post("https://aiproxy.sanand.workers.dev/openai/v1/chat/completions", json=payload, headers={
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        })

        extracted_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        extracted_card_number = "".join(re.findall(r"\d+", extracted_text))

        if len(extracted_card_number) < 12 or len(extracted_card_number) > 19:
            return {"error": "Invalid card number extracted"}, 500

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_card_number)

        return {"message": "Card number extracted and written to credit-card.txt"}
    except Exception as e:
        return {"error": str(e)}, 500

def sort_contacts():
    """Sort contacts in /data/contacts.json by last_name and first_name."""
    try:
        input_file = os.path.join(DATA_DIR, "contacts.json")
        output_file = os.path.join(DATA_DIR, "contacts-sorted.json")

        with open(input_file, "r", encoding="utf-8") as f:
            contacts = json.load(f)

        sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_contacts, f, indent=4)

        return {"message": "Contacts sorted successfully"}
    except Exception as e:
        return {"error": str(e)}, 500

def scrape_website(url, output_file):
    """Scrape website content and save as text file."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to fetch {url}, Status Code: {response.status_code}"}, 500

        soup = BeautifulSoup(response.text, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)

        text_output_path = os.path.join(DATA_DIR, output_file)
        with open(text_output_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        return {"message": f"Scraped content saved to {output_file}"}
    except Exception as e:
        return {"error": str(e)}, 500

def transcribe_audio():
    """Transcribe /data/audio.mp3 using Whisper AI."""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(os.path.join(DATA_DIR, "audio.mp3"))

        output_file = os.path.join(DATA_DIR, "audio-transcription.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["text"])

        return {"message": "Audio transcription saved"}
    except Exception as e:
        return {"error": str(e)}, 500
