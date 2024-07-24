from apscheduler.schedulers.background import BackgroundScheduler
from app.data_retrieval.stock_api import fetch_stock_data
from app.models.stock import Stock
import logging

def update_all_stocks():
    stocks = Stock.objects.all()
    for stock in stocks:
        try:
            fetch_stock_data(stock.symbol)  # This now includes fetching financial metrics
            logging.info(f"Updated data for {stock.symbol}")
        except Exception as e:
            logging.error(f"Failed to update {stock.symbol}: {str(e)}")

def update_specific_stock(symbol):
    try:
        fetch_stock_data(symbol)
        logging.info(f"Updated data for {symbol}")
    except Exception as e:
        logging.error(f"Failed to update {symbol}: {str(e)}")

def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_all_stocks, 'interval', minutes=60)  # Update every 5 minutes
    scheduler.start()