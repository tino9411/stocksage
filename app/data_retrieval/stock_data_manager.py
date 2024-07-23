from app.data_processing.stock_analysis import get_stock_summary
from app.data_retrieval.sec_scraper import SECScraper
from app.data_retrieval.stock_api import fetch_stock_data
from app.models.stock import Stock
import logging

class StockDataManager:
    def __init__(self):
        self.sec_scraper = SECScraper()

    def get_stock_summary(self, symbol):
        try:
            summary = get_stock_summary(symbol)
            if summary:
                logging.info(f"Successfully retrieved summary for {symbol}")
                return summary
            else:
                logging.warning(f"Stock not found: {symbol}")
                return {"error": "Stock not found or unable to retrieve data"}
        except Exception as e:
            logging.error(f"Unexpected error getting summary for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}

    def get_filing_info(self, symbol, filing_type):
        try:
            logging.info(f"Received request for {filing_type} filing info of {symbol}")
            get_info_func = getattr(self.sec_scraper, f"get_{filing_type.lower()}_filing_info")
            filing_info = get_info_func(symbol)
            if isinstance(filing_info, list) and filing_info:
                logging.info(f"Successfully retrieved {filing_type} filing info for {symbol}")
                return filing_info[0]
            elif isinstance(filing_info, dict) and "error" in filing_info:
                logging.warning(f"Error retrieving {filing_type} filing info for {symbol}: {filing_info['error']}")
                return filing_info
            else:
                logging.warning(f"Unexpected response format for {filing_type} filing info: {symbol}")
                return {"error": "Unexpected response format"}
        except Exception as e:
            logging.error(f"Unexpected error getting {filing_type} filing info for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}

    def get_full_report(self, filing_type, symbol):
        try:
            logging.info(f"Received request for full {filing_type} report of {symbol}")
            
            # Check if the report exists in the database
            stock = Stock.objects(symbol=symbol).first()
            if stock:
                existing_report = next((report for report in stock.sec_reports if report.filing_type == filing_type), None)
                if existing_report:
                    logging.info(f"Retrieved {filing_type} report for {symbol} from database")
                    return existing_report.full_text

            # If the report doesn't exist in the database, fetch it from SEC
            get_report_func = getattr(self.sec_scraper, f"get_{filing_type.lower()}_report")
            report = get_report_func(symbol)

            if "error" not in report:
                logging.info(f"Successfully retrieved and stored full {filing_type} report for {symbol}")
                return report["text"]
            else:
                logging.warning(f"Error retrieving full {filing_type} report for {symbol}: {report['error']}")
                return report
        except Exception as e:
            logging.error(f"Unexpected error getting full {filing_type} report for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}

    def get_financial_statement(self, symbol, statement_type):
        try:
            logging.info(f"Received request for {statement_type} of {symbol}")
            stock = fetch_stock_data(symbol)
            if stock:
                statement = getattr(stock, f"{statement_type}s", None)
                if statement:
                    statement_data = [stmt.to_mongo().to_dict() for stmt in statement]
                    for stmt in statement_data:
                        for key in ['date', 'fillingDate', 'acceptedDate']:
                            if key in stmt:
                                stmt[key] = stmt[key].isoformat()
                    logging.info(f"Successfully retrieved {statement_type} for {symbol}")
                    return statement_data
            logging.warning(f"{statement_type.capitalize()} not found for {symbol}")
            return {"error": f"{statement_type.capitalize()} not found or unable to retrieve data"}
        except Exception as e:
            logging.error(f"Unexpected error getting {statement_type} for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}

    def get_financial_metrics(self, symbol):
        try:
            logging.info(f"Received request for financial metrics of {symbol}")
            stock = fetch_stock_data(symbol)
            if stock and stock.financial_metrics:
                latest_metrics = stock.financial_metrics[0].to_mongo().to_dict()
                latest_metrics['date'] = latest_metrics['date'].isoformat()
                logging.info(f"Successfully retrieved financial metrics for {symbol}")
                return latest_metrics
            else:
                logging.warning(f"Financial metrics not found for {symbol}")
                return {"error": "Financial metrics not found or unable to retrieve data"}
        except Exception as e:
            logging.error(f"Unexpected error getting financial metrics for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}