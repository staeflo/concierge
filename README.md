# SciPaperConcierge

SciPaperConcierge is a tool designed to help researchers and students download academic papers remotely by sending a link via email to a specified email address. This is particularly useful for those who are off-campus and cannot access certain papers without being connected to a university network. 

## Features

- **Automated Email Checking**: Periodically checks an email inbox for new messages containing URLs of academic papers.
- **Paper Downloading**: Uses Selenium to automate the process of downloading papers from various journals based on predefined XPaths.
- **Automated Email Response**: Sends the downloaded paper as an email attachment back to the sender.

## How It Works

1. **Email Check**: The program checks the inbox for new, unread emails.
2. **URL Extraction**: It extracts the URL from the email body.
3. **Journal Identification**: Identifies the journal from the URL.
4. **Paper Downloading**: Uses Selenium to navigate to the URL and download the paper.
5. **Email Response**: Sends the downloaded paper back to the original sender as an email attachment.
6. **File Management**: Deletes the downloaded paper after sending the email to keep the download directory clean.

## Setup and Configuration

### Prerequisites

- Python 3.x
- Required Python packages:
  - `imaplib`
  - `email`
  - `smtplib`
  - `selenium`
  - `webdriver_manager`
  - `configparser`

### Configuration

1. **Email Credentials**: Store your email credentials in a `config.ini` file in the following format:
    ```ini
    [EMAIL]
    EMAIL = your-email@gmail.com
    PASSWORD = your-email-password
    ```

2. **Journal XPaths**: Ensure that the `xpaths` dictionary in the script contains the correct XPath expressions for the download buttons of the journals you are interested in. Here are some examples:
    ```python
    xpaths = {
        "nature": "/html/body/div[2]/main/article/div[2]/div[1]/div/div/a",
        "prl": "//button[@id='pdf-download']",
        "arxiv": "//*[@id='abs-outer']/div[2]/div[1]/ul/li[1]/a",
        "aps": "//*[@id='article-actions']/div/div/div/a[1]",
        "scipost": "/html/body/main/div[2]/div/ul/li[2]/a"
        # Add more journals and their XPaths here
    }
    ```

### Running the Program

1. **Install Dependencies**: Run the following command to install the required Python packages.

2. **Execute the Script**: Run the main script:
    ```bash
    python script_name.py
    ```

## Current Limitations and Issues and plans for Future Enhancements

1. **Non-Link Content Handling**: The program may crash if the email body contains content that is not a URL.
   -> Implement robust URL validation to handle non-link email content gracefully.
2. **Download Issues with Certain Journals**: Some journals, such as Nature, have overlays or banners that prevent direct downloading using the provided XPaths. Additional measures are needed to handle these cases.
   -> Improve the handling of download overlays and banners for journals like Nature.
3. **Network Restrictions**: The program must be run from within a university network to access certain journals.
   -> Explore alternative methods to bypass university network restrictions, such as VPN integration.


## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss any changes or enhancements.


---
