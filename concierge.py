import os
# To connect to the IMAP Server
import imaplib
# To process the email itself
import email
from email.header import decode_header
# To parse the URL inside of the message
from urllib.parse import urlparse
# To send emails through the web
import smtplib
import shutil

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
#Selenium to access a webbrowser and download the paper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Store Credentials on config.ini
import configparser


import time


# Define the path to the config file relative to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(script_dir, 'config.ini')

# Read credentials from config file
config = configparser.ConfigParser()
config.read(config_file_path)

if 'EMAIL' in config:
    EMAIL = config['EMAIL'].get('EMAIL', None)
    PASSWORD = config['EMAIL'].get('PASSWORD', None)
else:
    raise KeyError("The 'EMAIL' section is missing in the config.ini file")

if not EMAIL or not PASSWORD:
    raise ValueError("Email or password is missing in the config.ini file")

IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Dictionary with journal XPaths
xpaths = {
    "nature": "/html/body/div[2]/main/article/div[2]/div[1]/div/div/a", #Does not work due to strange overlay
    "prl": "//button[@id='pdf-download']",
    "arxiv": "//*[@id='abs-outer']/div[2]/div[1]/ul/li[1]/a",
    "aps": "//*[@id='article-actions']/div/div/div/a[1]",
    "scipost": "/html/body/main/div[2]/div/ul/li[2]/a"
    #"science": "/html/body/div[1]/div/div[1]/main/div[1]/article/header/div/div[5]/div[2]/div[3]/a/i" # Cannot access through Uni
    # Add more journals and their XPaths here
}


def check_email():
    try:
        # Connect to the IMAP server using a secure SSL connection.
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        # Log in to the specified email account with the provided credentials.
        mail.login(EMAIL, PASSWORD)
        # Select the "inbox" folder to perform operations on.
        mail.select('inbox')
        
        # Extract unread email IDs
        result, data = mail.search(None, '(UNSEEN)')
        email_ids = data[0].split()
        
        for email_id in email_ids:
            # Fetch the full email message (header, body, and attachments).
            result, message_data = mail.fetch(email_id, '(RFC822)')
            raw_email = message_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Initialize body variable
            body = ""

            # Check if the email message is multipart
            if msg.is_multipart():
                # Iterate over all parts of the email message
                for part in msg.walk():
                    content_type = part.get_content_type()
                    payload = part.get_payload(decode=True)
                    
                    # Skip empty payloads
                    if payload is None:
                        continue
                    
                    if content_type == 'text/plain':
                        body += payload.decode(errors='ignore').strip()
                    elif content_type == 'text/html':
                        # Handle HTML content if needed, for now, we're ignoring it
                        pass
            else:
                # If the email is not multipart, handle it directly
                payload = msg.get_payload(decode=True)
                if payload is not None:
                    body = payload.decode(errors='ignore').strip()

            # Return the sender's address and the body of the email
            return msg['From'], body
        
        # Close and log out of the email session
        mail.close()
        mail.logout()

        # Return None if no emails are found
        return None
    except imaplib.IMAP4.error as e:
        print("IMAP error:", e)
        return None
    except Exception as e:
        print("General error:", e)
        return None



# This function parses the URL from which we take the address and everything before .com is what we define as the journal name
def extract_journal_name(url):
    parsedurl = urlparse(url)
    domain = parsedurl.netloc
    return domain.split('.')[-2]




def download_paper(url,journal_name,download_dir):
    xpath = xpaths.get(journal_name)
    if not xpath:
        raise ValueError('XPath not found for the journal')
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    #Install webdriver
    driver = webdriver.Chrome(service = ChromeService(ChromeDriverManager().install()),options = options)

    try:
        driver.get(url)
        print(f"Accessing {url}")
        download_button = driver.find_element(By.XPATH, xpath)
        print(f"Download button found: {download_button}")
        before_files = set(os.listdir(download_dir))
        download_button.click()
        print("Download button clicked")
        # Before minus after is problematic if the file downloads to fast
        # It is a bit complicated to know the name of the file that was downloaded
        time.sleep(30)  # Adjust based on your download speed
        after_files = set(os.listdir(download_dir))
        
        new_files = after_files - before_files # This gives the downloaded file. If there are a lot of requests this might go wrong
        
        # If the file already exists one does not send a mail
        if new_files:
            downloaded_file = new_files.pop()
            file_path = os.path.join(download_dir, downloaded_file)
            print(f"New file found: {file_path}")
            return file_path
        else:
            print("No new files found.")
            return None
    except Exception as e:
        print(f"Error during downloading: {e}")
        return None
    finally:
        driver.quit()



def send_email(to_address , file_path):
    # This creates the Multipurpose Internet Mail Extensions (MIME) object including 'From', 'To' and 'Subject'
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to_address
    msg['Subject'] = 'Your requested paper'

    # Create MIMEBase Object
    part =MIMEBase('application','octet-stream')
    # Opens the file specified by file_path in binary read mode
    with open(file_path, 'rb') as file:
        part.set_payload(file.read())
        # Base64 encoding is used to ensure that the binary data can be safely transmitted as text in the email.
    encoders.encode_base64(part)
    # Adding the Content-Disposition Header
    part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(file_path)}"')
    msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER,SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL,PASSWORD)
        server.send_message(msg)

    # Delete the file after sending the email to avoid that it is not sent when you download it at a later point
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Failed to delete {file_path}. Reason: {e}")



def main():
    base_download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    download_dir = os.path.join(base_download_dir, "Scipaperconcierge")

    # Create the directory if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Created download directory: {download_dir}")
    else:
        print(f"Download directory already exists: {download_dir}")
    
    while True:
        print("Checking for new emails...")
        result = check_email()
        if result:
            from_address, paper_url = result
            print(f"New email received from: {from_address}")
            print(f"Paper URL found: {paper_url}")
            
            journal_name = extract_journal_name(paper_url)
            print(f"Extracted journal name: {journal_name}")
            
            print("Starting paper download...")
            file_path = download_paper(paper_url, journal_name, download_dir)
            print(file_path)
            if file_path:
                print(f"Paper downloaded successfully: {file_path}")
                print("Sending email with the downloaded paper...")
                send_email(from_address, file_path)
                print(f"Email sent to: {from_address} with attachment: {file_path}")
            else:
                print("Failed to send the paper.")
        else:
            print("No new emails found.")
        
        print("Waiting for 60 seconds before checking again...")
        time.sleep(60)

if __name__ == "__main__":
    main()

