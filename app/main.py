from flask import Flask, jsonify, request
from app.database.mongodb import initialize_db
from app.data_processing.stock_analysis import get_stock_summary
from app.scheduler.jobs import init_scheduler
from app.data_retrieval.sec_scraper import SECScraper
import logging
from flask_cors import CORS

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

@app.route('/api/10k_report/<symbol>')
def get_10k_report_route(symbol):
    return get_filing_report(symbol, "10-K", sec_scraper.get_10k_report)

@app.route('/api/10q_report/<symbol>')
def get_10q_report_route(symbol):
    return get_filing_report(symbol, "10-Q", sec_scraper.get_10q_report)

@app.route('/api/full_report/<filing_type>/<symbol>')
def get_full_report(filing_type, symbol):
    try:
        logging.info(f"Received request for full {filing_type} report of {symbol}")
        if filing_type == "10-K":
            report = sec_scraper.get_10k_report(symbol)
        elif filing_type == "10-Q":
            report = sec_scraper.get_10q_report(symbol)
        else:
            return jsonify({"error": "Invalid filing type"}), 400

        if "error" not in report:
            logging.info(f"Successfully retrieved full {filing_type} report for {symbol}")
            return report["text"], 200, {'Content-Type': 'text/plain'}
        else:
            logging.warning(f"Error retrieving full {filing_type} report for {symbol}: {report['error']}")
            return jsonify(report), 404
    except Exception as e:
        logging.error(f"Unexpected error getting full {filing_type} report for stock {symbol}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)