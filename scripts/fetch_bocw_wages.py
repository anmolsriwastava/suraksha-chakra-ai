"""
fetch_bocw_wages.py

Downloads an official government PDF to test the RAG extraction pipeline.
"""
import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
RAW_DIR = os.path.join("data", "raw", "bocw")
os.makedirs(RAW_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_sample():
    url = "https://www.india.gov.in/sites/upload_files/npi/files/minimum_wages_act.pdf"
    filename = "Minimum_Wages_Act_Official.pdf"
    filepath = os.path.join(RAW_DIR, filename)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, verify=False)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        logging.info(f"Successfully downloaded {filename}")
    except Exception as e:
        logging.error(f"Failed to download: {e}")

if __name__ == "__main__":
    fetch_sample()
    pdfs = [f for f in os.listdir(RAW_DIR) if f.endswith(".pdf")]
    logging.info(f"Total PDFs collected: {len(pdfs)}")
