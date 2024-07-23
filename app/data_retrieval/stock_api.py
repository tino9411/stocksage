import yfinance as yf
from app.models.stock import Stock, HistoricalData
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)

def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        logging.debug(f"Raw data from yfinance for {symbol}: {info}")
        
        stock_doc = Stock.objects(symbol=symbol).first()
        if not stock_doc:
            stock_doc = Stock(symbol=symbol)
        
        stock_doc.company_name = info.get('longName', '') or info.get('shortName', '')
        stock_doc.sector = info.get('sector', '')
        stock_doc.industry = info.get('industry', '')
        
        # Fallback mechanisms for current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        
        stock_doc.current_data = {
            'price': current_price,
            'volume': info.get('volume') or info.get('regularMarketVolume'),
            'average_volume': info.get('averageVolume') or info.get('averageDailyVolume10Day'),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
            'forward_pe': info.get('forwardPE'),
            'dividend_yield': info.get('dividendYield'),
            '52_week_high': info.get('fiftyTwoWeekHigh'),
            '52_week_low': info.get('fiftyTwoWeekLow'),
            'beta': info.get('beta'),
            'eps': info.get('trailingEps') or info.get('forwardEps'),
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        hist = stock.history(start=start_date, end=end_date)
        
        stock_doc.historical_data = [
            HistoricalData(
                date=date.to_pydatetime(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume'])
            ) for date, row in hist.iterrows()
        ]
        
        stock_doc.financial_ratios = {
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'ebitda': info.get('ebitda'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'peg_ratio': info.get('pegRatio'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'free_cash_flow': info.get('freeCashflow'),
        }
        
        # Calculate growth rates if possible
        if 'earningsGrowth' in info or 'revenueGrowth' in info:
            stock_doc.growth_rates = {
                'earnings_growth': info.get('earningsGrowth'),
                'revenue_growth': info.get('revenueGrowth'),
            }
        
        stock_doc.last_updated = datetime.now(timezone.utc)
        stock_doc.save()
        
        logging.info(f"Successfully updated data for {symbol}")
        logging.debug(f"Processed data for {symbol}: {stock_doc.to_json()}")
        return stock_doc
    
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
        raise