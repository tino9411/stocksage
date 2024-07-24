from app.data_processing.stock_analysis import get_stock_summary
from app.data_retrieval.sec_scraper import SECScraper
from app.data_retrieval.stock_api import fetch_stock_data, fetch_income_statement, fetch_balance_sheet, fetch_cash_flow_statement, fetch_key_metrics
from app.models.stock import Stock
import logging
from datetime import timezone, datetime

class StockDataManager:
    def __init__(self):
        self.sec_scraper = SECScraper()

    def get_stock_summary(self, symbol):
        try:
            stock = fetch_stock_data(symbol)
            if stock:
                summary = {
                    "symbol": stock.symbol,
                    "companyName": stock.companyName,
                    "currency": stock.currency,
                    "exchange": stock.exchange,
                    "industry": stock.industry,
                    "sector": stock.sector,
                    "description": stock.description,
                    "website": stock.website,
                    "ceo": stock.ceo,
                    "ipoDate": stock.ipoDate,
                    "isActivelyTrading": stock.isActivelyTrading,
                    "last_updated": stock.last_updated.isoformat()
                }

                if stock.real_time_quote:
                    real_time_data = {
                        "price": stock.real_time_quote.price,
                        "changesPercentage": stock.real_time_quote.changesPercentage,
                        "change": stock.real_time_quote.change,
                        "dayLow": stock.real_time_quote.dayLow,
                        "dayHigh": stock.real_time_quote.dayHigh,
                        "yearHigh": stock.real_time_quote.yearHigh,
                        "yearLow": stock.real_time_quote.yearLow,
                        "marketCap": stock.real_time_quote.marketCap,
                        "priceAvg50": stock.real_time_quote.priceAvg50,
                        "priceAvg200": stock.real_time_quote.priceAvg200,
                        "volume": stock.real_time_quote.volume,
                        "avgVolume": stock.real_time_quote.avgVolume,
                        "open": stock.real_time_quote.open,
                        "previousClose": stock.real_time_quote.previousClose,
                        "eps": stock.real_time_quote.eps,
                        "pe": stock.real_time_quote.pe,
                        "earningsAnnouncement": stock.real_time_quote.earningsAnnouncement.isoformat() if stock.real_time_quote.earningsAnnouncement else None,
                        "sharesOutstanding": stock.real_time_quote.sharesOutstanding,
                        "timestamp": stock.real_time_quote.timestamp.isoformat() if stock.real_time_quote.timestamp else None,
                    }
                    summary.update(real_time_data)
                else:
                    logging.warning(f"Real-time quote missing for {symbol}")
                    summary["real_time_quote_missing"] = True

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

    def get_financial_statement(self, symbol, statement_type, years=5):
        try:
            logging.info(f"Received request for {statement_type} of {symbol} for the last {years} years")
            stock = fetch_stock_data(symbol)
            if stock:
                if statement_type == 'income_statement':
                    statement = fetch_income_statement(symbol, years)
                elif statement_type == 'balance_sheet':
                    statement = fetch_balance_sheet(symbol, years)
                elif statement_type == 'cash_flow_statement':
                    statement = fetch_cash_flow_statement(symbol, years)
                else:
                    return {"error": f"Invalid statement type: {statement_type}"}

                if statement:
                    statement_data = [stmt.to_mongo().to_dict() for stmt in statement]
                    for stmt in statement_data:
                        for key in ['date', 'fillingDate', 'acceptedDate']:
                            if key in stmt and stmt[key]:
                                stmt[key] = stmt[key].isoformat()
                    logging.info(f"Successfully retrieved {statement_type} for {symbol}")
                    return statement_data
                else:
                    logging.warning(f"{statement_type.capitalize()} not found for {symbol}")
                    return {"error": f"{statement_type.capitalize()} not found or unable to retrieve data"}
            else:
                logging.warning(f"Stock data not found for {symbol}")
                return {"error": f"Stock data not found for {symbol}"}
        except Exception as e:
            logging.error(f"Unexpected error getting {statement_type} for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}
        
    def get_key_metrics(self, symbol, years=5, period=None):
        try:
            logging.info(f"Received request for key metrics of {symbol} for the past {years} years")
            stock = Stock.objects(symbol=symbol).first()
            if not stock:
                stock = fetch_stock_data(symbol)
            
            if stock:
                # Check if we have recent key metrics data
                if stock.key_metrics:
                    latest_metric = max(stock.key_metrics, key=lambda x: x.date)
                    now = datetime.now(timezone.utc)
                    latest_metric_date = latest_metric.date.replace(tzinfo=timezone.utc) if latest_metric.date.tzinfo is None else latest_metric.date
                    if (now - latest_metric_date).days < 1:
                        logging.info(f"Using cached key metrics for {symbol}")
                        metrics = stock.key_metrics
                    else:
                        metrics = fetch_key_metrics(symbol, years)
                        if metrics:
                            stock.key_metrics = metrics
                            stock.save()
                else:
                    metrics = fetch_key_metrics(symbol, years)
                    if metrics:
                        stock.key_metrics = metrics
                        stock.save()

                if metrics:
                    if period:
                        metrics = [m for m in metrics if m.period == period]
                    
                    metrics_data = []
                    for km in metrics:
                        metric_dict = km.to_mongo().to_dict()
                        if 'date' in metric_dict and metric_dict['date']:
                            metric_dict['date'] = metric_dict['date'].replace(tzinfo=timezone.utc).isoformat()
                        metric_dict = {k: v for k, v in metric_dict.items() if v is not None}
                        metrics_data.append(metric_dict)
                    
                    logging.info(f"Successfully retrieved key metrics for {symbol}")
                    return metrics_data
                else:
                    logging.warning(f"Key metrics not found for {symbol}")
                    return {"error": f"Key metrics not found or unable to retrieve data"}
            else:
                logging.warning(f"Stock data not found for {symbol}")
                return {"error": f"Stock data not found for {symbol}"}
        except Exception as e:
            logging.error(f"Unexpected error getting key metrics for stock {symbol}: {str(e)}")
            return {"error": "An unexpected error occurred"}
