import numpy as np
from app.models.stock import Stock
from app.data_retrieval.stock_api import fetch_stock_data
import logging
from datetime import datetime, timedelta, timezone

def calculate_moving_average(prices, window):
    if len(prices) < window:
        return None
    return np.convolve(prices, np.ones(window), 'valid')[-1] / window

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(period - 1) + upval)/period
        down = (down*(period - 1) + downval)/period
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)

    return rsi[-1]

def get_stock_summary(stock_symbol):
    try:
        stock = fetch_stock_data(stock_symbol)
        
        if not stock:
            logging.error(f"No stock data found for {stock_symbol}")
            return None

        prices = [data.close for data in stock.historical_data]

        if not prices:
            logging.error(f"No historical price data found for {stock_symbol}")
            return None

        sma_50 = calculate_moving_average(prices, 50)
        sma_200 = calculate_moving_average(prices, 200)
        rsi = calculate_rsi(prices)

        summary = {
            "symbol": stock.symbol,
            "company_name": stock.company_name,
            "sector": stock.sector,
            "industry": stock.industry,
            "current_price": stock.current_data.get('price'),
            "volume": stock.current_data.get('volume'),
            "average_volume": stock.current_data.get('average_volume'),
            "market_cap": stock.current_data.get('market_cap'),
            "beta": stock.current_data.get('beta'),
            "pe_ratio": stock.current_data.get('pe_ratio'),
            "forward_pe": stock.current_data.get('forward_pe'),
            "eps": stock.current_data.get('eps'),
            "dividend_yield": stock.current_data.get('dividend_yield'),
            "52_week_high": stock.current_data.get('52_week_high'),
            "52_week_low": stock.current_data.get('52_week_low'),
            "50_day_ma": sma_50,
            "200_day_ma": sma_200,
            "rsi": rsi,
            "return_on_equity": stock.financial_ratios.get('return_on_equity'),
            "return_on_assets": stock.financial_ratios.get('return_on_assets'),
            "profit_margin": stock.financial_ratios.get('profit_margin'),
            "operating_margin": stock.financial_ratios.get('operating_margin'),
            "price_to_book": stock.financial_ratios.get('price_to_book'),
            "price_to_sales": stock.financial_ratios.get('price_to_sales'),
            "peg_ratio": stock.financial_ratios.get('peg_ratio'),
            "debt_to_equity": stock.financial_ratios.get('debt_to_equity'),
            "current_ratio": stock.financial_ratios.get('current_ratio'),
            "quick_ratio": stock.financial_ratios.get('quick_ratio'),
            "free_cash_flow": stock.financial_ratios.get('free_cash_flow'),
            "ebitda": stock.financial_ratios.get('ebitda'),
        }

        if hasattr(stock, 'growth_rates'):
            summary.update({
                "earnings_growth": stock.growth_rates.get('earnings_growth'),
                "revenue_growth": stock.growth_rates.get('revenue_growth'),
            })

         # Add cash flow statement data to the summary
        if stock.cash_flow_statements:
            latest_cash_flow = stock.cash_flow_statements[0]
            summary.update({
                "operating_cash_flow": latest_cash_flow.operatingCashFlow,
                "capital_expenditure": latest_cash_flow.capitalExpenditure,
                "free_cash_flow": latest_cash_flow.freeCashFlow,
                "net_cash_provided_by_operating_activities": latest_cash_flow.netCashProvidedByOperatingActivities,
                "net_cash_used_for_investing_activities": latest_cash_flow.netCashUsedForInvestingActivites,
                "net_cash_used_provided_by_financing_activities": latest_cash_flow.netCashUsedProvidedByFinancingActivities,
            })

        # Remove None values
        summary = {k: v for k, v in summary.items() if v is not None}

        logging.info(f"Stock summary for {stock_symbol}: {summary}")
        return summary
    except Exception as e:
        logging.error(f"Error in get_stock_summary for {stock_symbol}: {str(e)}", exc_info=True)
        raise