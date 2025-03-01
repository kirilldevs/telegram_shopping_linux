import os
import json
import openpyxl
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import csv

# Load environment variables
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# File paths
json_dir = "telegram_data"
analyzed_folder = "analyzed_tables"
description_file = "files/full_description.txt"
log_file = "files/script.log"

# Ensure necessary directories exist
os.makedirs(analyzed_folder, exist_ok=True)

# Generate filename based on the current date (DD-MM-YYYY.xlsx)
current_date = datetime.now().strftime("%d-%m-%Y")
output_csv = os.path.join(analyzed_folder, f"{current_date}.csv")

# Logging function
def log(message):
    """Write logs to both console and a file."""
    formatted_message = f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] {message}"
    print(formatted_message)
    with open(log_file, "a", encoding="utf-8") as log_f:
        log_f.write(formatted_message + "\n")

def load_latest_json():
    """Find and load the latest JSON file with Telegram posts."""
    if not os.path.exists(json_dir):
        log("No JSON directory found!")
        return None
    
    json_files = sorted(
        [f for f in os.listdir(json_dir) if f.endswith(".json")],
        reverse=True
    )

    if not json_files:
        log("No JSON files found!")
        return None

    latest_json_path = os.path.join(json_dir, json_files[0])
    log(f"Loading JSON file: {latest_json_path}")

    with open(latest_json_path, "r", encoding="utf-8") as file:
        return json.load(file)

def load_full_description():
    """Load the detailed user description for filtering."""
    if not os.path.exists(description_file):
        log("Description file not found!")
        return ""
    
    with open(description_file, "r", encoding="utf-8") as file:
        return file.read().strip()

def clean_json_response(response_text):
    """Cleans GPT response by removing markdown formatting like ```json ... ```."""
    if response_text.startswith("```json"):
        response_text = response_text[7:]  # Remove leading ```json
    if response_text.endswith("```"):
        response_text = response_text[:-3]  # Remove trailing ```
    return response_text.strip()

def extract_relevant_info(posts):
    """Extract product, description, price, and determine relevance using GPT-4o-mini."""
    extracted_data = []
    full_description = load_full_description()

    for post in posts:
        text = post.get("text", "")
        link = post.get("link", "N/A")

        prompt = f"""
        Extract the following details from the given post and return as JSON:
        [
            {{
                "product_name": "Extracted product name",
                "short_description": "Extracted short description",
                "price": "Exact price or price range",
                "relevance": "YES/NO/MAYBE based on the description compare",
                "link": "{link}"
            }}
        ]
        **Description to compare with**: {full_description}
        
        **Post**: {text}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )

            # Extract response and clean it
            gpt_response = response.choices[0].message.content.strip()
            cleaned_response = clean_json_response(gpt_response)  # Remove formatting

            try:
                # Ensure response is always a list
                parsed_response = json.loads(cleaned_response)
                if isinstance(parsed_response, dict):
                    parsed_response = [parsed_response]  # Convert single object to list

                for product_data in parsed_response:
                    extracted_data.append([
                        product_data.get("product_name", "Unknown"),
                        product_data.get("short_description", "N/A"),
                        product_data.get("price", "Unknown"),
                        product_data.get("relevance", "MAYBE"),
                        product_data.get("link", "N/A")
                    ])
                    log(f"Processed product: {product_data.get('product_name', 'Unknown')}")

            except json.JSONDecodeError:
                log(f"Invalid JSON format from GPT response:\n{gpt_response}")
                extracted_data.append(["Error", "Error", "Error", "Error", link])

        except Exception as e:
            log(f"Error processing post: {e}")
            extracted_data.append(["Error", "Error", "Error", "Error", link])

    return extracted_data

def save_to_csv(data):
    """Save extracted data to a CSV file with UTF-8 BOM encoding for proper Hebrew support in Excel."""
    
    # Headers
    headers = ["Product", "Description", "Price", "Is What I'm Looking For", "Link"]

    # Save to CSV with UTF-8 BOM encoding
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        # Write headers
        writer.writerow(headers)

        # Write data rows
        for row in data:
            writer.writerow(row)

    log(f"Saved analysis to {output_csv}")

def main():
    log("Starting analysis script...")
    
    posts = load_latest_json()
    if posts:
        extracted_data = extract_relevant_info(posts)
        save_to_csv(extracted_data)

    log("Analysis script completed.")

if __name__ == "__main__":
    main()
