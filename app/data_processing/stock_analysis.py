import numpy as np
from app.models.stock import Stock
from app.data_retrieval.stock_api import fetch_stock_data
from app.data_processing.technical_indicators import (
    calculate_ema, calculate_macd, calculate_bollinger_bands,
    calculate_stochastic_oscillator, calculate_atr, calculate_obv,
    calculate_peg_ratio, calculate_debt_to_ebitda, calculate_roic,
    calculate_dividend_growth_rate
)
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
        high_prices = [data.high for data in stock.historical_data]
        low_prices = [data.low for data in stock.historical_data]
        volumes = [data.volume for data in stock.historical_data]

        if not prices:
            logging.error(f"No historical price data found for {stock_symbol}")
            return None

        sma_50 = calculate_moving_average(prices, 50)
        sma_200 = calculate_moving_average(prices, 200)
        rsi = calculate_rsi(prices)

        ema_20 = calculate_ema(prices, 20)
        macd, signal, histogram = calculate_macd(prices)
        upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(prices)
        stoch_k, stoch_d = calculate_stochastic_oscillator(prices, low_prices, high_prices)
        atr = calculate_atr(high_prices, low_prices, prices)
        obv = calculate_obv(prices, volumes)

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
            "20_day_ema": ema_20,
            "macd": macd,
            "macd_signal": signal,
            "macd_histogram": histogram,
            "bollinger_upper": upper_bb,
            "bollinger_middle": middle_bb,
            "bollinger_lower": lower_bb,
            "stochastic_k": stoch_k,
            "stochastic_d": stoch_d,
            "atr": atr,
            "obv": obv,
        }

        # Add financial ratios
        summary.update(stock.financial_ratios)

        # Add growth rates
        if hasattr(stock, 'growth_rates'):
            summary.update(stock.growth_rates)

        # Add cash flow statement data
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

        # Add financial metrics
        if stock.financial_metrics:
            latest_metrics = stock.financial_metrics[0]
            summary.update({
                "financial_metrics_date": latest_metrics.date,
                "financial_metrics_year": latest_metrics.calendarYear,
                "financial_metrics_period": latest_metrics.period,
                "revenue_per_share": latest_metrics.revenuePerShare,
                "net_income_per_share": latest_metrics.netIncomePerShare,
                "operating_cash_flow_per_share": latest_metrics.operatingCashFlowPerShare,
                "free_cash_flow_per_share": latest_metrics.freeCashFlowPerShare,
                "cash_per_share": latest_metrics.cashPerShare,
                "book_value_per_share": latest_metrics.bookValuePerShare,
                "tangible_book_value_per_share": latest_metrics.tangibleBookValuePerShare,
                "shareholders_equity_per_share": latest_metrics.shareholdersEquityPerShare,
                "interest_debt_per_share": latest_metrics.interestDebtPerShare,
                "market_cap": latest_metrics.marketCap,
                "enterprise_value": latest_metrics.enterpriseValue,
                "pe_ratio": latest_metrics.peRatio,
                "price_to_sales_ratio": latest_metrics.priceToSalesRatio,
                "pocf_ratio": latest_metrics.pocfratio,
                "pfcf_ratio": latest_metrics.pfcfRatio,
                "pb_ratio": latest_metrics.pbRatio,
                "ptb_ratio": latest_metrics.ptbRatio,
                "ev_to_sales": latest_metrics.evToSales,
                "enterprise_value_over_ebitda": latest_metrics.enterpriseValueOverEBITDA,
                "ev_to_operating_cash_flow": latest_metrics.evToOperatingCashFlow,
                "ev_to_free_cash_flow": latest_metrics.evToFreeCashFlow,
                "earnings_yield": latest_metrics.earningsYield,
                "free_cash_flow_yield": latest_metrics.freeCashFlowYield,
                "debt_to_equity": latest_metrics.debtToEquity,
                "debt_to_assets": latest_metrics.debtToAssets,
                "net_debt_to_ebitda": latest_metrics.netDebtToEBITDA,
                "current_ratio": latest_metrics.currentRatio,
                "interest_coverage": latest_metrics.interestCoverage,
                "income_quality": latest_metrics.incomeQuality,
                "dividend_yield": latest_metrics.dividendYield,
                "payout_ratio": latest_metrics.payoutRatio,
                "sales_general_and_administrative_to_revenue": latest_metrics.salesGeneralAndAdministrativeToRevenue,
                "research_and_development_to_revenue": latest_metrics.researchAndDdevelopementToRevenue,
                "intangibles_to_total_assets": latest_metrics.intangiblesToTotalAssets,
                "capex_to_operating_cash_flow": latest_metrics.capexToOperatingCashFlow,
                "capex_to_revenue": latest_metrics.capexToRevenue,
                "capex_to_depreciation": latest_metrics.capexToDepreciation,
                "stock_based_compensation_to_revenue": latest_metrics.stockBasedCompensationToRevenue,
                "graham_number": latest_metrics.grahamNumber,
                "roic": latest_metrics.roic,
                "return_on_tangible_assets": latest_metrics.returnOnTangibleAssets,
                "graham_net_net": latest_metrics.grahamNetNet,
                "working_capital": latest_metrics.workingCapital,
                "tangible_asset_value": latest_metrics.tangibleAssetValue,
                "net_current_asset_value": latest_metrics.netCurrentAssetValue,
                "invested_capital": latest_metrics.investedCapital,
                "average_receivables": latest_metrics.averageReceivables,
                "average_payables": latest_metrics.averagePayables,
                "average_inventory": latest_metrics.averageInventory,
                "days_sales_outstanding": latest_metrics.daysSalesOutstanding,
                "days_payables_outstanding": latest_metrics.daysPayablesOutstanding,
                "days_of_inventory_on_hand": latest_metrics.daysOfInventoryOnHand,
                "receivables_turnover": latest_metrics.receivablesTurnover,
                "payables_turnover": latest_metrics.payablesTurnover,
                "inventory_turnover": latest_metrics.inventoryTurnover,
                "roe": latest_metrics.roe,
                "capex_per_share": latest_metrics.capexPerShare
            })

            # Calculate additional ratios
            if stock.income_statement and stock.balance_sheets:
                latest_income = stock.income_statement[0]
                latest_balance = stock.balance_sheets[0]
                
                peg_ratio = calculate_peg_ratio(
                    summary['pe_ratio'], 
                    summary.get('earnings_growth', 0)
                )
                debt_to_ebitda = calculate_debt_to_ebitda(
                    latest_balance.totalDebt, 
                    latest_income.ebitda
                )
                roic = calculate_roic(
                    latest_income.netIncome,
                    latest_cash_flow.dividendsPaid,
                    latest_balance.totalDebt,
                    latest_balance.totalStockholdersEquity
                )
                
                summary.update({
                    "peg_ratio": peg_ratio,
                    "debt_to_ebitda": debt_to_ebitda,
                    "roic": roic
                })

            # Calculate dividend growth rate if applicable
            if stock.cash_flow_statements and len(stock.cash_flow_statements) >= 2:
                dividends = [stmt.dividendsPaid for stmt in stock.cash_flow_statements]
                years = len(dividends)
                dividend_growth_rate = calculate_dividend_growth_rate(dividends, years)
                summary["dividend_growth_rate"] = dividend_growth_rate

        # Remove None values
        summary = {k: v for k, v in summary.items() if v is not None}

        logging.info(f"Stock summary for {stock_symbol}: {summary}")
        return summary
    except Exception as e:
        logging.error(f"Error in get_stock_summary for {stock_symbol}: {str(e)}", exc_info=True)
        raise