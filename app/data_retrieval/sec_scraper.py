import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import logging
import html2text

def get_filing_info(symbol, filing_type):
    try:
        # Step 1: Get the CIK
        cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={symbol}&Find=Search&owner=exclude&action=getcompany"
        response = requests.get(cik_url, headers={'User-Agent': 'StockSage vincenzo.riccardi.jobs@gmail.com'})
        soup = BeautifulSoup(response.content, 'html.parser')
        cik_re = re.compile(r'CIK=(\d{10})')
        cik_match = cik_re.search(str(soup))
        if not cik_match:
            return {"error": f"CIK not found for symbol {symbol}"}
        cik = cik_match.group(1)

        # Step 2: Get the latest filing
        edgar_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}&dateb=&owner=exclude&count=1"
        response = requests.get(edgar_url, headers={'User-Agent': 'StockSage vincenzo.riccardi.jobs@gmail.com'})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the link to the filing detail page
        filing_detail_link = soup.select_one('table.tableFile2 td:nth-of-type(2) a')
        if not filing_detail_link:
            return {"error": f"No {filing_type} filing found for symbol {symbol}"}
        filing_detail_url = f"https://www.sec.gov{filing_detail_link['href']}"

        # Get the accepted date
        accepted_date_elem = soup.select_one('table.tableFile2 td:nth-of-type(3)')
        accepted_date = accepted_date_elem.text.strip() if accepted_date_elem else None

        # Step 3: Get the actual document link
        response = requests.get(filing_detail_url, headers={'User-Agent': 'StockSage vincenzo.riccardi.jobs@gmail.com'})
        soup = BeautifulSoup(response.content, 'html.parser')
        doc_link = soup.select_one(f'table.tableFile tr:has(td:contains("{filing_type}")) a')
        if not doc_link:
            return {"error": f"{filing_type} document link not found for symbol {symbol}"}
        doc_url = f"https://www.sec.gov{doc_link['href']}"

        # Correct the final link to remove '/ix?doc='
        doc_href = doc_link['href']
        if '/ix?doc=' in doc_href:
            doc_url = f"https://www.sec.gov{doc_href.replace('/ix?doc=', '')}"
        else:
            doc_url = f"https://www.sec.gov{doc_href}"

        # Format dates
        try:
            accepted_datetime = datetime.strptime(accepted_date, "%Y-%m-%d")
            formatted_accepted_date = accepted_datetime.strftime("%Y-%m-%d %H:%M:%S")
            formatted_filing_date = accepted_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            logging.warning(f"Unable to parse date: {accepted_date}")
            formatted_accepted_date = accepted_date
            formatted_filing_date = accepted_date

        return [{
            "symbol": symbol,
            "cik": cik,
            "type": filing_type,
            "link": filing_detail_url,
            "finalLink": doc_url,
            "acceptedDate": formatted_accepted_date,
            "fillingDate": formatted_filing_date
        }]
    except Exception as e:
        logging.error(f"Error fetching {filing_type} filing info for {symbol}: {str(e)}")
        return {"error": f"Failed to fetch {filing_type} filing info: {str(e)}"}

def get_10k_filing_info(symbol):
    return get_filing_info(symbol, "10-K")

def get_10q_filing_info(symbol):
    return get_filing_info(symbol, "10-Q")

def download_filing_content(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'StockSage vincenzo.riccardi.jobs@gmail.com'})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error downloading filing content: {str(e)}")
        return None

def process_filing_content(content):
    # Convert HTML to plain text
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    text = h.handle(content)

    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    return text.strip()

def get_filing_report(symbol, filing_type):
    try:
        filing_info = get_filing_info(symbol, filing_type)
        if isinstance(filing_info, dict) and "error" in filing_info:
            return filing_info

        doc_url = filing_info[0]["finalLink"]
        content = download_filing_content(doc_url)
        
        if content is None:
            return {"error": f"Failed to download {filing_type} content"}

        processed_text = process_filing_content(content)
        
        # Truncate if too long (adjust the length as needed for your GPT model)
        max_length = 500000  # Adjust based on your GPT model's token limit
        truncated_text = processed_text[:max_length] + "..." if len(processed_text) > max_length else processed_text
        
        return {
            "text": truncated_text,
            "url": doc_url,
            "retrieved_at": datetime.utcnow().isoformat(),
            "full_text_length": len(processed_text),
            "truncated": len(processed_text) > max_length
        }
    except Exception as e:
        logging.error(f"Error fetching {filing_type} report for {symbol}: {str(e)}")
        return {"error": f"Failed to fetch {filing_type} report: {str(e)}"}

def get_10k_report(symbol):
    return get_filing_report(symbol, "10-K")

def get_10q_report(symbol):
    return get_filing_report(symbol, "10-Q")