from flask import Flask, jsonify, request
from app.database.mongodb import initialize_db
from app.data_processing.stock_analysis import get_stock_summary
from app.scheduler.jobs import init_scheduler
from app.data_retrieval.sec_scraper import SECScraper
from app.data_retrieval.stock_api import fetch_stock_data
import logging
from flask_cors import CORS
from app.models.stock import Stock

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}) 
logging.basicConfig(level=logging.DEBUG)

initialize_db()
init_scheduler()

# Initialize the SECScraper
sec_scraper = SECScraper()

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.debug('Response Status: %s', response.status)
    app.logger.debug('Response Headers: %s', response.headers)
    return response

@app.route('/api/stock_summary/<symbol>')
def stock_summary(symbol):
    try:
        logging.info(f"Received request for stock summary of {symbol}")
        summary = get_stock_summary(symbol)
        if summary:
            logging.info(f"Successfully retrieved summary for {symbol}")
            return jsonify(summary), 200
        else:
            logging.warning(f"Stock not found: {symbol}")
            return jsonify({"error": "Stock not found or unable to retrieve data"}), 404
    except Exception as e:
        logging.error(f"Unexpected error getting summary for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def get_filing_info(symbol, filing_type, get_info_func):
    try:
        logging.info(f"Received request for {filing_type} filing info of {symbol}")
        filing_info = get_info_func(symbol)
        if isinstance(filing_info, list) and filing_info:
            logging.info(f"Successfully retrieved {filing_type} filing info for {symbol}")
            return jsonify(filing_info[0]), 200
        elif isinstance(filing_info, dict) and "error" in filing_info:
            logging.warning(f"Error retrieving {filing_type} filing info for {symbol}: {filing_info['error']}")
            return jsonify(filing_info), 404
        else:
            logging.warning(f"Unexpected response format for {filing_type} filing info: {symbol}")
            return jsonify({"error": "Unexpected response format"}), 500
    except Exception as e:
        logging.error(f"Unexpected error getting {filing_type} filing info for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/10k_filing/<symbol>')
def get_10k_filing(symbol):
    return get_filing_info(symbol, "10-K", sec_scraper.get_10k_filing_info)

@app.route('/api/10q_filing/<symbol>')
def get_10q_filing(symbol):
    return get_filing_info(symbol, "10-Q", sec_scraper.get_10q_filing_info)

@app.route('/api/8k_filing/<symbol>')
def get_8k_filing(symbol):
    return get_filing_info(symbol, "8-K", sec_scraper.get_8k_filing_info)

@app.route('/api/def14a_filing/<symbol>')
def get_def_14a_filing(symbol):
    return get_filing_info(symbol, "DEF-14A", sec_scraper.get_def_14a_filing_info)

@app.route('/api/s1_filing/<symbol>')
def get_s1_filing(symbol):
    return get_filing_info(symbol, "S-1", sec_scraper.get_s1_filing_info)

@app.route('/api/form4_filing/<symbol>')
def get_form4_filing(symbol):
    return get_filing_info(symbol, "4", sec_scraper.get_form4_filing_info)

@app.route('/api/13d_filing/<symbol>')
def get_13d_filing(symbol):
    return get_filing_info(symbol, "SC-13D", sec_scraper.get_13d_filing_info)

@app.route('/api/13g_filing/<symbol>')
def get_13g_filing(symbol):
    return get_filing_info(symbol, "SC 13G", sec_scraper.get_13g_filing_info)

@app.route('/api/20f_filing/<symbol>')
def get_20f_filing(symbol):
    return get_filing_info(symbol, "20-F", sec_scraper.get_20f_filing_info)

def get_filing_report(symbol, filing_type, get_report_func):
    try:
        logging.info(f"Received request for {filing_type} report of {symbol}")
        report = get_report_func(symbol)
        if "error" not in report:
            logging.info(f"Successfully retrieved {filing_type} report for {symbol}")
            return jsonify({
                "url": report["url"],
                "retrieved_at": report["retrieved_at"],
                "full_text_length": report["full_text_length"],
                "truncated": report["truncated"],
                "text_preview": report["text"][:1000] + "..."  # Send only a preview in the JSON response
            }), 200
        else:
            logging.warning(f"Error retrieving {filing_type} report for {symbol}: {report['error']}")
            return jsonify(report), 404
    except Exception as e:
        logging.error(f"Unexpected error getting {filing_type} report for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/full_report/<filing_type>/<symbol>')
def get_full_report(filing_type, symbol):
    try:
        logging.info(f"Received request for full {filing_type} report of {symbol}")
        
        # Check if the report exists in the database
        stock = Stock.objects(symbol=symbol).first()
        if stock:
            existing_report = next((report for report in stock.sec_reports if report.filing_type == filing_type), None)
            if existing_report:
                logging.info(f"Retrieved {filing_type} report for {symbol} from database")
                return existing_report.full_text, 200, {'Content-Type': 'text/plain'}

        # If the report doesn't exist in the database, fetch it from SEC
        if filing_type == "10-K":
            report = sec_scraper.get_10k_report(symbol)
        elif filing_type == "10-Q":
            report = sec_scraper.get_10q_report(symbol)
        elif filing_type == "8-K":
            report = sec_scraper.get_8k_report(symbol)
        elif filing_type == "DEF-14A":
            report = sec_scraper.get_def_14a_report(symbol)
        elif filing_type == "S-1":
            report = sec_scraper.get_s1_report(symbol)
        elif filing_type == "4":
            report = sec_scraper.get_form4_report(symbol)
        elif filing_type == "SC-13D":
            report = sec_scraper.get_13d_report(symbol)
        elif filing_type == "SC-13G":
            report = sec_scraper.get_13g_report(symbol)
        elif filing_type == "20-F":
            report = sec_scraper.get_20f_report(symbol)
        else:
            return jsonify({"error": "Invalid filing type"}), 400

        if "error" not in report:
            logging.info(f"Successfully retrieved and stored full {filing_type} report for {symbol}")
            return report["text"], 200, {'Content-Type': 'text/plain'}
        else:
            logging.warning(f"Error retrieving full {filing_type} report for {symbol}: {report['error']}")
            return jsonify(report), 404
    except Exception as e:
        logging.error(f"Unexpected error getting full {filing_type} report for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/income_statement/<symbol>')
def get_income_statement(symbol):
    try:
        logging.info(f"Received request for income statement of {symbol}")
        stock = fetch_stock_data(symbol)
        if stock and stock.income_statement:
            income_statement = [stmt.to_mongo().to_dict() for stmt in stock.income_statement]
            for stmt in income_statement:
                stmt['date'] = stmt['date'].isoformat()
            logging.info(f"Successfully retrieved income statement for {symbol}")
            return jsonify(income_statement), 200
        else:
            logging.warning(f"Income statement not found for {symbol}")
            return jsonify({"error": "Income statement not found or unable to retrieve data"}), 404
    except Exception as e:
        logging.error(f"Unexpected error getting income statement for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)