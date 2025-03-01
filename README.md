## Telegram Shopping Automation

This project automates **monitoring Telegram shopping groups** and **extracting relevant posts** based on user-defined keywords.\
It uses **Telethon** to read messages from groups you have joined and stores the extracted posts for analysis.

## Disclaimer

- **This script must only be used in groups where you are legally a member.**
- **Do not use this for mass data collection, spamming, or violating Telegram's ToS.**
- **The author is not responsible for any misuse of this script.**
- **Using a personal account for automation may result in restrictions from Telegram. Use at your own risk.**

## Features

- Reads messages from Telegram groups you are a member of.
- Extracts posts based on **keywords** defined in `files/keywords.txt`.
- Stores extracted messages in **JSON and CSV format**.
- Generates **daily HTML summaries** of saved messages.
- Uses **GPT API** to analyze and categorize posts.
- Automates everything with **cron jobs**.

## Installation & Setup

### 1. Clone the Repository

```
git clone https://github.com/kirilldevs/telegram_shopping_linux.git
cd telegram_shopping_linux
```

### 2. Create a Virtual Environment

```
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Set Up API Credentials

Create a `.env` file in the project root with:

```
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
TELEGRAM_PHONE_NUMBER=YOUR_PHONE_NUMBER
TELEGRAM_BUY_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
```

Make sure `** is in **` to prevent exposing sensitive data.

## Usage

### Run the Script

```
python main.py
```

This will:

1. **Read messages from Telegram groups**.
2. **Filter posts based on keywords** in `files/keywords.txt`.
3. **Save extracted posts** to JSON and CSV.
4. **Generate an HTML summary**.

### Automating with Cron

To run `actions.py` **daily at 21:00**, add this to `crontab -e`:

```
0 21 * * * cd /opt/python_projects/telegram_shopping && /opt/python_projects/telegram_shopping/venv/bin/python actions.py >> actions.log 2>&1
```

## Data Output

- **JSON Data**: `telegram_data/YYYY-MM-DD.json`
- **CSV Export**: `analyzed_tables/YYYY-MM-DD.csv`
- **HTML Summary**: `html/YYYY-MM-DD.html`
- **Logs**: `files/script.log`

## How Keywords Work

Modify `files/keywords.txt` to track **specific products**:

```
laptop
keyboard, bluetooth
ssd
```

- **Single words** match if they appear in any part of the message.
- **Multiple words (comma-separated)** require **all words to appear** in the message (even if they’re not together).

## Potential Issues & Fixes

### 1. "Missing `keywords.txt`"

If `main.py` stops with **"Missing keywords.txt"**, ensure the file exists in:

```
/opt/python_projects/telegram_shopping/files/keywords.txt
```

### 2. "Today's JSON file not found"

- **Fix:** Run `main.py` manually:
  ```
  python main.py
  ```
- If that works, **update your cron job** to use the correct working directory.

### 3. "GitHub Authentication Failed"

GitHub no longer supports password authentication. Use a **Personal Access Token (PAT):**

```
git remote set-url origin https://YOUR_GITHUB_USERNAME:YOUR_PAT@github.com/kirilldevs/telegram_shopping_linux.git
```

Then push:

```
git push -u origin main
```

## License

This project is licensed under the **MIT License**.

## Contributing

Pull requests are welcome! Open an issue if you find a bug or have a feature request.

