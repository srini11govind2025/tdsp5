from fastapi import FastAPI, HTTPException, Query
import os
import subprocess
import json
from pathlib import Path
import sqlite3
import requests
from pydantic import BaseModel

app = FastAPI()

# Define the base data directory to ensure we only work within this path
DATA_DIR = Path("/data")

# Ensure data directory security
def secure_path_check(path: Path):
    if not path.resolve().is_relative_to(DATA_DIR):
        raise HTTPException(status_code=403, detail="Access outside /data is prohibited")

# AIPROXY setup
AIPROXY_BASE_URL = "https://aiproxy.sanand.workers.dev/openai"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

# Helper functions for handling specific tasks
def run_subprocess(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Subprocess failed: {str(e)}")

# Task A1
def install_uv_and_run_script(email):
    # Ensure 'uv' is installed and then run the script with the email as an argument
    run_subprocess(["pip", "install", "uv"])
    run_subprocess(["python3", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", email])

# Task A2
def format_file_with_prettier():
    run_subprocess(["npx", "prettier@3.4.2", "--write", DATA_DIR / "format.md"])

# Task A3
def count_wednesdays():
    dates_file = DATA_DIR / "dates.txt"
    secure_path_check(dates_file)
    with dates_file.open() as f:
        wednesdays = sum(1 for line in f if "Wednesday" in line)
    output_file = DATA_DIR / "dates-wednesdays.txt"
    with output_file.open("w") as f:
        f.write(str(wednesdays))

# Task A4
def sort_contacts():
    contacts_file = DATA_DIR / "contacts.json"
    secure_path_check(contacts_file)
    with contacts_file.open() as f:
        contacts = json.load(f)
    sorted_contacts = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))
    output_file = DATA_DIR / "contacts-sorted.json"
    with output_file.open("w") as f:
        json.dump(sorted_contacts, f, indent=2)

# Task A5
def get_recent_logs():
    logs_dir = DATA_DIR / "logs"
    secure_path_check(logs_dir)
    log_files = sorted(logs_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
    output_file = DATA_DIR / "logs-recent.txt"
    with output_file.open("w") as f:
        for log_file in log_files:
            with log_file.open() as log:
                f.write(log.readline())

# Task A6
def extract_markdown_titles():
    docs_dir = DATA_DIR / "docs"
    secure_path_check(docs_dir)
    index = {}
    for md_file in docs_dir.glob("*.md"):
        with md_file.open() as f:
            for line in f:
                if line.startswith("# "):
                    index[md_file.name] = line.strip("# ").strip()
                    break
    output_file = DATA_DIR / "index.json"
    with output_file.open("w") as f:
        json.dump(index, f)

# Task A7 - Using LLM for email extraction
def extract_email_sender():
    email_file = DATA_DIR / "email.txt"
    secure_path_check(email_file)
    with email_file.open() as f:
        email_content = f.read()
    
    # Call AI Proxy for email extraction using LLM
    response = requests.post(
        f"{AIPROXY_BASE_URL}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": f"Extract sender's email from this: {email_content}"}]
        }
    )
    result = response.json().get("choices", [])[0].get("message", {}).get("content", "").strip()
    output_file = DATA_DIR / "email-sender.txt"
    with output_file.open("w") as f:
        f.write(result)

# Task A8 - Using LLM for credit card extraction
def extract_credit_card():
    image_file = DATA_DIR / "credit-card.png"
    secure_path_check(image_file)
    
    # Call AI Proxy for credit card extraction using LLM
    response = requests.post(
        f"{AIPROXY_BASE_URL}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": f"Extract the credit card number from this image: {image_file}"}]
        }
    )
    result = response.json().get("choices", [])[0].get("message", {}).get("content", "").strip().replace(" ", "")
    output_file = DATA_DIR / "credit-card.txt"
    with output_file.open("w") as f:
        f.write(result)

# Task A9 - Find the most similar comments using embeddings
def find_similar_comments():
    comments_file = DATA_DIR / "comments.txt"
    secure_path_check(comments_file)
    with comments_file.open() as f:
        comments = f.readlines()
    
    # Call AI Proxy for embeddings
    response = requests.post(
        f"{AIPROXY_BASE_URL}/v1/embeddings",
        headers={
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "text-embedding-3-small",
            "input": comments
        }
    )
    embeddings = response.json().get("data", [])
    
    # Find the most similar pair based on embeddings
    # (Similarity calculation logic to be added here)

    output_file = DATA_DIR / "comments-similar.txt"
    with output_file.open("w") as f:
        # Write the most similar comments (This is a placeholder)
        f.write("\n".join(comments[:2]))  # Example placeholder

# Task A10 - Query SQLite database for ticket sales
def total_gold_ticket_sales():
    db_file = DATA_DIR / "ticket-sales.db"
    secure_path_check(db_file)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(price * units) FROM tickets WHERE type='Gold'")
    result = cursor.fetchone()[0]
    output_file = DATA_DIR / "ticket-sales-gold.txt"
    with output_file.open("w") as f:
        f.write(str(result))
    conn.close()

# Task B3: Fetch data from an API and save it
def fetch_api_data():
    api_url = "https://api.example.com/data"
    response = requests.get(api_url)
    data = response.json()
    output_file = DATA_DIR / "api-data.json"
    with output_file.open("w") as f:
        json.dump(data, f)

# Task B4: Clone a git repo and make a commit
def git_clone_and_commit():
    repo_url = "https://github.com/example/repo.git"
    repo_dir = DATA_DIR / "repo"
    run_subprocess(["git", "clone", repo_url, repo_dir])
    with open(repo_dir / "file.txt", "w") as f:
        f.write("New content")
    run_subprocess(["git", "add", "."], cwd=repo_dir)
    run_subprocess(["git", "commit", "-m", "Added new content"], cwd=repo_dir)

# Task B5: Run a SQL query on a SQLite or DuckDB database
def query_database():
    db_file = DATA_DIR / "database.db"
    secure_path_check(db_file)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    output_file = DATA_DIR / "db-query-results.txt"
    with output_file.open("w") as f:
        f.write(json.dumps(result))
    conn.close()

# Task B6: Extract data from a website (web scraping)
# Task B7: Compress or resize an image
def resize_image():
    image_file = DATA_DIR / "image.png"
    secure_path_check(image_file)
    output_file = DATA_DIR / "image-resized.png"
    run_subprocess(["convert", image_file, "-resize", "50%", output_file])

# Task B8: Transcribe audio from an MP3 file
def transcribe_audio():
    audio_file = DATA_DIR / "audio.mp3"
    secure_path_check(audio_file)
    output_file = DATA_DIR / "audio-transcription.txt"
    run_subprocess(["ffmpeg", "-i", audio_file, output_file])

# Task B9: Convert Markdown to HTML
def convert_markdown_to_html():
    markdown_file = DATA_DIR / "doc.md"
    secure_path_check(markdown_file)
    output_file = DATA_DIR / "doc.html"
    run_subprocess(["pandoc", markdown_file, "-o", output_file])

# Task B10: Write an API endpoint that filters a CSV file and returns JSON data
def filter_csv_file():
    csv_file = DATA_DIR / "data.csv"
    secure_path_check(csv_file)
    output_file = DATA_DIR / "filtered.json"
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
        filtered_rows = [row for row in reader if row['status'] == 'active']
    with open(output_file, 'w') as f:
        json.dump(filtered_rows, f)



# API endpoints
@app.post("/run")
async def run_task(task: str):
    if "install uv" in task and "datagen.py" in task:
        install_uv_and_run_script("23f1002634@ds.study.iitm.ac.in")  # Replace with actual user email
    elif "format" in task:
        format_file_with_prettier()
    elif "count" in task:
        count_wednesdays()
    elif "sort contacts" in task:
        sort_contacts()
    elif "recent logs" in task:
        get_recent_logs()
    elif "extract markdown" in task:
        extract_markdown_titles()
    elif "email sender" in task:
        extract_email_sender()
    elif "credit card" in task:
        extract_credit_card()
    elif "similar comments" in task:
        find_similar_comments()
    elif "ticket sales" in task:
        total_gold_ticket_sales()
    # Task B handling
    elif "fetch api data" in task:
        fetch_api_data()
    elif "git commit" in task:
        git_clone_and_commit()
    elif "query database" in task:
        query_database()
    elif "resize image" in task:
        resize_image()
    elif "transcribe audio" in task:
        transcribe_audio()
    elif "markdown to html" in task:
        convert_markdown_to_html()
    elif "filter csv" in task:
        filter_csv_file()
    else:
        raise HTTPException(status_code=400, detail="Task not recognized")
    
    return {"status": "success"}

@app.get("/read")
async def read_file(path: str):
    file_path = DATA_DIR / path
    secure_path_check(file_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    with file_path.open() as f:
        content = f.read()
    
    return content

# Main entry point for the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)