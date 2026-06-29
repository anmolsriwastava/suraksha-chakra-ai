import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PDF_SOURCES = [
    {
        "url": "https://clc.gov.in/clc/sites/default/files/Minimum%20Wages%20VDA%2001.04.2024.pdf",
        "filename": "clc_minimum_wages_2024.pdf"
    },
    {
        "url": "https://labour.gov.in/sites/default/files/bocw_act_1996.pdf",
        "filename": "central_bocw_act_1996.pdf"
    },
    {
        "url": "https://labour.gov.in/sites/default/files/gazette_notification_bocw_wages.pdf",
        "filename": "gazette_bocw_wages.pdf"
    }
]

def main():
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting BOCW PDF ingestion...")
    for source in PDF_SOURCES:
        url = source["url"]
        filename = source["filename"]
        target_path = raw_dir / filename
        
        if target_path.exists():
            logger.info(f"Skipping {filename}, already exists.")
            continue
            
        logger.info(f"Downloading {url}...")
        try:
            # We use a standard user agent to avoid being blocked by simple WAFs
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                # Basic check to avoid saving HTML blocks
                if b"<html" not in resp.content[:20].lower():
                    with open(target_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"Successfully downloaded {filename}")
                else:
                    logger.warning(f"Failed to download {filename} - Received HTML instead of PDF")
            else:
                logger.warning(f"Failed to download {filename} - Status {resp.status_code}")
                logger.warning(f"Note: Manual PDF placement may be required for {filename}")
        except Exception as e:
            logger.error(f"Exception while downloading {filename}: {e}")
            logger.warning(f"Note: Manual PDF placement may be required for {filename}")

if __name__ == "__main__":
    main()
