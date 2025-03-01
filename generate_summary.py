
import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot credentials
bot_token = os.getenv("TELEGRAM_BUY_BOT_TOKEN")  # Telegram bot token
api_id = int(os.getenv("TELEGRAM_API_ID"))  # Telegram API ID
api_hash = os.getenv("TELEGRAM_API_HASH")  # Telegram API Hash
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))  # Chat ID where the file will be sent

# File paths
files_dir = "files"
json_dir = "telegram_data"
html_dir = "html"
log_file = os.path.join(files_dir, "script.log")
current_date = datetime.now().strftime("%d-%m-%Y")  # Format date as DD-MM-YYYY
html_file_path = os.path.join(html_dir, f"{current_date}.html")

# Ensure necessary directories exist
os.makedirs(files_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)
os.makedirs(html_dir, exist_ok=True)

# Logging function
def log(message):
    """Write logs to both console and a file."""
    formatted_message = f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] {message}"
    print(formatted_message)
    with open(log_file, "a", encoding="utf-8") as log_f:
        log_f.write(formatted_message + "\n")

def load_latest_json():
    """Load only today's JSON file to ensure posts are filtered correctly."""
    today_filename = datetime.now().strftime("%d-%m-%Y") + ".json"
    today_json_path = os.path.join(json_dir, today_filename)

    if not os.path.exists(today_json_path):
        log(f"Today's JSON file not found: {today_json_path}")
        return None

    log(f"Loading today's JSON file: {today_json_path}")

    with open(today_json_path, "r", encoding="utf-8") as file:
        return json.load(file)


    latest_json_path = os.path.join(json_dir, json_files[0])
    log(f"Loading JSON file: {latest_json_path}")

    with open(latest_json_path, "r", encoding="utf-8") as file:
        return json.load(file)

def generate_html(posts):
    """Generate an HTML summary from the collected Telegram posts."""
    if not posts:
        log("No posts to include in the summary!")
        return

    date_str = datetime.now().strftime("%d/%m/%Y")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Telegram Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; direction: rtl; text-align: right; margin: 20px; background-color: #f4f4f4; }}
            .container {{ background: white; padding: 20px; border-radius: 10px; max-width: 800px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ text-align: center; color: #333; }}
            .post {{ border-bottom: 1px solid #ddd; padding: 10px 0; }}
            .post:last-child {{ border-bottom: none; }}
            .keywords {{ font-weight: bold; color: #007bff; }}
            .source {{ font-size: 14px; color: #666; }}
            .date {{ font-size: 12px; color: #888; }}
            .text {{ margin: 10px 0; }}
            .link {{ color: blue; text-decoration: underline; word-wrap: break-word; }}
        </style>
    </head>
    <body>

    <div class="container">
        <h1>סיכום יומי - {date_str}</h1>
    """

    for post in posts:
        keywords = ", ".join(post.get("matched_keywords", []))
        text = post["text"].replace("\n", "<br>")

        # Extract first link from the message
        link = post.get("link", "")
        link_html = f'<a class="link" href="{link}">{link}</a>' if link else "ללא קישור"

        html_content += f"""
        <div class="post">
            <div class="keywords">מילות מפתח: {keywords}</div>
            <div class="source">מקור: {post["group_name"]}</div>
            <div class="date">{post["date"]}</div>
            <div class="text">
                {text} <br>
                {link_html}
            </div>
        </div>
        """

    html_content += """
    </div>
    </body>
    </html>
    """

    # Save to file
    with open(html_file_path, "w", encoding="utf-8") as file:
        file.write(html_content)

    log(f"Generated HTML summary: {html_file_path}")

async def send_html_as_file():
    """Sends the generated HTML summary as a file to Telegram using a bot."""
    if not os.path.exists(html_file_path):
        log("HTML file not found! Exiting.")
        return

    # Initialize the client and start it correctly
    client = TelegramClient("bot_session", api_id, api_hash)

    await client.start(bot_token=bot_token)  # Ensure the bot is started before sending
    await client.send_file(TELEGRAM_CHAT_ID, html_file_path, caption="Daily Telegram Summary")

    log("HTML summary sent as file successfully!")
    await client.disconnect()  # Properly disconnect after sending


async def send_summary_as_message(posts):
    """Sends the summary as a Telegram message in smaller chunks if needed."""
    if not posts:
        log("No posts available to send as a message!")
        return

    message_parts = []
    current_message = f"Daily Telegram Summary - {datetime.now().strftime('%d-%m-%Y')}\n\n"
    char_limit = 4000  # Telegram's limit (slightly lower to avoid issues)

    for post in posts:
        keywords = ", ".join(post.get("matched_keywords", []))
        text = post["text"]
        link = post.get("link", "")

        post_content = f"**{post['group_name']}**\n{post['date']}\nKeywords: {keywords}\n{text}\n"
        if link:
            post_content += f"🔗 {link}\n"
        post_content += "\n" + "=" * 30 + "\n\n"

        if len(current_message) + len(post_content) > char_limit:
            message_parts.append(current_message)  # Store full message
            current_message = ""  # Reset for next chunk

        current_message += post_content  # Add new post

    if current_message:
        message_parts.append(current_message)  # Append last chunk

    client = TelegramClient("bot_session", api_id, api_hash)
    await client.start(bot_token=bot_token)

    for msg in message_parts:
        await client.send_message(TELEGRAM_CHAT_ID, msg, parse_mode="md", link_preview=False)

    log("Summary sent as multiple messages successfully.")
    await client.disconnect()


async def main():
    log("Starting summary generation...")

    posts = load_latest_json()
    if posts:
        generate_html(posts)

        # Uncomment the desired function:
        await send_html_as_file()      # Sends as a file
        await send_summary_as_message(posts)  # Sends as a text message

    log("Summary generation completed.")

if __name__ == "__main__":
    asyncio.run(main())
