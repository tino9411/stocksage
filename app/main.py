from flask import Flask, jsonify, request, render_template_string
from app.database.mongodb import initialize_db
from app.scheduler.jobs import init_scheduler
from app.data_retrieval.stock_data_manager import StockDataManager
from app.assistant.assistant import StockAnalysisAssistant
import logging
from flask_cors import CORS
import os
import markdown2

stock_analysis_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ symbol }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
        }
        h2, h3, h4 {
            color: #34495e;
        }
        .analysis {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <h1>{{ symbol }}</h1>
    <div class="analysis">
        {{ analysis | safe }}
    </div>
</body>
</html>
"""

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
logging.basicConfig(level=logging.DEBUG)

initialize_db()
init_scheduler()

stock_data_manager = StockDataManager()

# Load the assistant ID from an environment variable or create a new one
ASSISTANT_ID = os.getenv('STOCK_ASSISTANT_ID')
if ASSISTANT_ID:
    stock_assistant = StockAnalysisAssistant(stock_data_manager, assistant_id=ASSISTANT_ID)
    logging.info(f"Loaded existing assistant with ID: {ASSISTANT_ID}")
else:
    stock_assistant = StockAnalysisAssistant(stock_data_manager)
    ASSISTANT_ID = stock_assistant.assistant.id
    logging.info(f"Created new assistant with ID: {ASSISTANT_ID}")
    # You might want to save this ID for future use, e.g., to an environment variable

@app.route('/api/stock_summary/<symbol>')
def stock_summary(symbol):
    return jsonify(stock_data_manager.get_stock_summary(symbol))

@app.route('/api/<filing_type>_filing/<symbol>')
def get_filing(filing_type, symbol):
    return jsonify(stock_data_manager.get_filing_info(symbol, filing_type))

@app.route('/api/full_report/<filing_type>/<symbol>')
def get_full_report(filing_type, symbol):
    report = stock_data_manager.get_full_report(filing_type, symbol)
    if isinstance(report, str):
        return report, 200, {'Content-Type': 'text/plain'}
    else:
        return jsonify(report)

@app.route('/api/<statement_type>/<symbol>')
@app.route('/api/<statement_type>/<symbol>/<int:years>')
def get_financial_statement(statement_type, symbol, years=5):
    return jsonify(stock_data_manager.get_financial_statement(symbol, statement_type, years))

@app.route('/api/key_metrics/<symbol>')
@app.route('/api/key_metrics/<symbol>/<int:years>')
def get_key_metrics(symbol, years=5):
    period = request.args.get('period')
    return jsonify(stock_data_manager.get_key_metrics(symbol, years, period))

@app.route('/api/analyze_stock/<symbol>')
def analyze_stock(symbol):
    try:
        logging.info(f"Received request for stock analysis of {symbol}")
        analysis = stock_assistant.analyze_stock(symbol)
        if analysis:
            logging.info(f"Successfully generated analysis for {symbol}")
            html_content = markdown2.markdown(analysis)
            return render_template_string(stock_analysis_template, symbol=symbol, analysis=html_content)
        else:
            logging.warning(f"Failed to generate analysis for {symbol}")
            return jsonify({"error": "Failed to generate analysis"}), 500
    except Exception as e:
        logging.error(f"Unexpected error analyzing stock {symbol}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/watchlist')
def get_watchlist():
    # Static watchlist
    watchlist = [
        {'symbol': 'AAPL', 'companyName': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'companyName': 'Alphabet Inc.'},
        {'symbol': 'MSFT', 'companyName': 'Microsoft Corporation'},
        {'symbol': 'AMZN', 'companyName': 'Amazon.com, Inc.'},
        {'symbol': 'FB', 'companyName': 'Meta Platforms, Inc.'},
    ]
    return jsonify(watchlist)

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        # Preflight request. Reply successfully:
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.json
        stock_symbol = data.get('stock')
        message = data.get('message')
        conversation_history = data.get('conversation_history', [])

        if not stock_symbol or not message:
            return jsonify({"error": "Missing stock symbol or message"}), 400

        response = stock_assistant.process_stock_conversation(stock_symbol, message, conversation_history)
        
        # Convert Markdown to HTML for easier rendering on the frontend
        html_response = markdown2.markdown(response)
        
        return jsonify({"message": html_response})
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)