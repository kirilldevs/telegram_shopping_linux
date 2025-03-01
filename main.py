#fksdfsdk
import os
import json
import asyncio
import re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(BASE_DIR, "files")
json_dir = os.path.join(BASE_DIR, "telegram_data")
log_file = os.path.join(files_dir, "script.log")
LAST_ID_FILE = os.path.join(files_dir, "last_post_id.json")
keywords_file = os.path.join(files_dir, "keywords.txt")
groups_file = os.path.join(files_dir, "telegram_groups.txt")

# Ensure necessary directories exist
os.makedirs(files_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)

# Telegram API credentials
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")
phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")

# Get current time and 24-hour time window
current_utc_time = datetime.now(timezone.utc)
time_window = current_utc_time - timedelta(hours=24)

# Global variable for last post ID
LAST_POST_ID = 0

# Logging function
def log(message):
    """Write logs to both console and a file."""
    formatted_message = f"[{current_time()}] {message}"
    print(formatted_message)
    with open(log_file, "a", encoding="utf-8") as log_f:
        log_f.write(formatted_message + "\n")

def current_time():
    """Returns the current time as a formatted string."""
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def load_last_post_id():
    """Load the last used post ID from a file."""
    global LAST_POST_ID
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r", encoding="utf-8") as file:
            try:
                LAST_POST_ID = json.load(file).get("last_id", 0)
            except json.JSONDecodeError:
                LAST_POST_ID = 0
    else:
        LAST_POST_ID = 0

def save_last_post_id():
    """Save the last used post ID to a file."""
    with open(LAST_ID_FILE, "w", encoding="utf-8") as file:
        json.dump({"last_id": LAST_POST_ID}, file, ensure_ascii=False, indent=4)

def generate_post_id():
    """Generate a unique post ID, incrementing it in memory."""
    global LAST_POST_ID
    LAST_POST_ID += 1
    return LAST_POST_ID

def load_keywords():
    """Load keywords from a text file, distinguishing single words and grouped words."""
    if not os.path.exists(keywords_file):
        log("Keyword file not found.")
        return []

    keywords = []
    with open(keywords_file, "r", encoding="utf-8") as file:
        for line in file:
            words = [word.strip().lower() for word in line.strip().split(",")]
            keywords.append(words)  # Store single words and groups as lists

    return keywords


def find_matching_keywords(text, keyword_list):
    """Find keywords or keyword groups that match the message text."""
    text_lower = text.lower()
    matching_keywords = []

    for words in keyword_list:
        if isinstance(words, list) and len(words) > 1:  # If it's a keyword group (multiple words)
            if all(word in text_lower for word in words):
                matching_keywords.append(", ".join(words))  # Store group as a string
        elif isinstance(words, list) and len(words) == 1:  # If it's a single keyword
            word = words[0]
            if word in text_lower:
                matching_keywords.append(word)

    return matching_keywords



def extract_first_link(text):
    """Extract the first URL from the text that starts with 'https'."""
    match = re.search(r"https?://\S+", text)
    return match.group(0) if match else None

def load_existing_posts(json_file):
    """Load existing posts to avoid duplicates."""
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    return []

def save_message_if_relevant(message, group_name, json_file):
    """Save only messages that contain relevant keywords."""
    keywords = load_keywords()
    if not keywords or not message.text.strip():
        return False  # No keywords or empty message → Ignore
    
    matching_keywords = find_matching_keywords(message.text, keywords)

    if matching_keywords:  # Only save if keywords are found
        posts = load_existing_posts(json_file)
        link = extract_first_link(message.text)

        new_message = {
            "post_id": generate_post_id(),
            "date": message.date.strftime("%d-%m-%Y %H:%M:%S"),
            "text": message.text,
            "source": "Telegram",
            "group_name": group_name,
            "matched_keywords": matching_keywords,
            "link": link
        }
        posts.append(new_message)

        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(posts, file, ensure_ascii=False, indent=4)

        log(f"Saved post from {group_name} (Post ID: {new_message['post_id']}) | Keywords: {', '.join(matching_keywords)} | Link: {link}")
        return True

    return False  # No keyword match → Ignore message


def load_groups():
    """Load Telegram group IDs from a file, ignoring commented lines."""
    groups = []
    if not os.path.exists(groups_file):
        log("Groups file not found.")
        return groups
    with open(groups_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=")
            try:
                group_id = int(value)
                group_name = key.replace("TELEGRAM_GROUP_ID_", "").replace("_", " ").title()
                groups.append((group_id, group_name))
            except ValueError:
                log(f"Invalid group ID in line: {line}")
    return groups


async def fetch_group_messages(client, group_id, group_name):
    """Fetch all messages from a specific group that were sent in the last 24 hours."""
    json_file = os.path.join(json_dir, f"{current_utc_time.strftime('%d-%m-%Y')}.json")
    post_count = 0
    scanned_count = 0

    try:
        async for message in client.iter_messages(group_id):
            scanned_count += 1
            msg_date = message.date.replace(tzinfo=timezone.utc)

            if msg_date < time_window:
                break  # Stop fetching messages once we reach an older one

            if message.text:
                if save_message_if_relevant(message, group_name, json_file):
                    post_count += 1

    except Exception as e:
        log(f"Critical error in {group_name}: {e}")

    log(f"{group_name} | {post_count} posts saved | {scanned_count} messages scanned")
    return post_count, scanned_count

async def main():
    """Main function to process multiple groups."""
    global LAST_POST_ID

    load_last_post_id()  # Load last ID once

    groups = load_groups()
    total_posts = 0
    total_scanned = 0  

    if not groups:
        log("No groups found.")
        return

    session_path = os.path.join(BASE_DIR, "session")
    async with TelegramClient(session_path, api_id, api_hash) as client:
        await client.start(phone_number)

        for group_id, group_name in groups:
            posts_saved, messages_scanned = await fetch_group_messages(client, group_id, group_name)
            total_posts += posts_saved
            total_scanned += messages_scanned  

    save_last_post_id()  # Save last ID once at the end

    log(f"{len(groups)} groups | {total_posts} posts saved | {total_scanned} messages scanned")

if __name__ == "__main__":
    asyncio.run(main())

