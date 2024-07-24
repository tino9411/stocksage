import yfinance as yf
from app.models.stock import Stock, HistoricalData, FinancialStatement, BalanceSheet, CashFlowStatement, FinancialMetrics
from datetime import datetime, timezone, timedelta
import logging
import requests
import os
from dotenv import load_dotenv
from mongoengine.errors import ValidationError

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

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
        
       # Fetch and store income statement data
        income_statement = fetch_income_statement(symbol)
        if income_statement:
            stock_doc.income_statement = income_statement

        stock_doc.last_updated = datetime.now(timezone.utc)
        stock_doc.save()
        
         # Fetch and store balance sheet data
        balance_sheets = fetch_balance_sheet(symbol)
        if balance_sheets:
            stock_doc.balance_sheets = balance_sheets

        stock_doc.last_updated = datetime.now(timezone.utc)
        stock_doc.save()
        
        # Fetch and store cash flow statement data
        cash_flow_statements = fetch_cash_flow_statement(symbol)
        if cash_flow_statements:
            stock_doc.cash_flow_statements = cash_flow_statements

        stock_doc.last_updated = datetime.now(timezone.utc)
        stock_doc.save()
        
        # Fetch and store financial metrics
        financial_metrics = fetch_financial_metrics(symbol)
        if financial_metrics:
            stock_doc.financial_metrics = financial_metrics

        stock_doc.last_updated = datetime.now(timezone.utc)
        stock_doc.save()

        logging.info(f"Successfully updated data for {symbol}")
        logging.debug(f"Processed data for {symbol}: {stock_doc.to_json()}")
        return stock_doc
    
    except Exception as e:
        logging.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
        raise

def fetch_income_statement(symbol, years=5, force_refresh=False):
    try:
        stock = Stock.objects(symbol=symbol).first()
        
        # Check if we already have recent income statements (e.g., less than 1 day old)
        if not force_refresh and stock and stock.income_statement:
            latest_statement = stock.income_statement[0]
            if (datetime.now(timezone.utc) - latest_statement.date.replace(tzinfo=timezone.utc)).days < 1:
                logging.info(f"Using cached income statements for {symbol}")
                return stock.income_statement

        # If no recent data, fetch from FMP API
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        annual_url = f"{FMP_BASE_URL}/income-statement/{symbol}?period=annual&limit={years}&apikey={FMP_API_KEY}"
        quarterly_url = f"{FMP_BASE_URL}/income-statement/{symbol}?period=quarter&limit={years * 4}&apikey={FMP_API_KEY}"

        annual_response = requests.get(annual_url)
        annual_response.raise_for_status()
        annual_data = annual_response.json()

        try:
            quarterly_response = requests.get(quarterly_url)
            quarterly_response.raise_for_status()
            quarterly_data = quarterly_response.json()
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch quarterly data for {symbol}: {str(e)}")
            quarterly_data = []

        if not annual_data and not quarterly_data:
            logging.warning(f"No income statement data found for {symbol}")
            return None

        income_statements = []
        
        for statement in annual_data + quarterly_data:
            statement_date = datetime.strptime(statement['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if statement_date < start_date:
                continue
            
            financial_statement = FinancialStatement(
                date=statement_date,
                symbol=statement['symbol'],
                reportedCurrency=statement['reportedCurrency'],
                cik=statement['cik'],
                fillingDate=datetime.strptime(statement['fillingDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc),
                acceptedDate=datetime.strptime(statement['acceptedDate'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc),
                calendarYear=statement['calendarYear'],
                period=statement['period'],
                revenue=statement['revenue'],
                costOfRevenue=statement['costOfRevenue'],
                grossProfit=statement['grossProfit'],
                grossProfitRatio=statement['grossProfitRatio'],
                researchAndDevelopmentExpenses=statement['researchAndDevelopmentExpenses'],
                generalAndAdministrativeExpenses=statement['generalAndAdministrativeExpenses'],
                sellingAndMarketingExpenses=statement['sellingAndMarketingExpenses'],
                sellingGeneralAndAdministrativeExpenses=statement['sellingGeneralAndAdministrativeExpenses'],
                otherExpenses=statement['otherExpenses'],
                operatingExpenses=statement['operatingExpenses'],
                costAndExpenses=statement['costAndExpenses'],
                interestIncome=statement['interestIncome'],
                interestExpense=statement['interestExpense'],
                depreciationAndAmortization=statement['depreciationAndAmortization'],
                ebitda=statement['ebitda'],
                ebitdaratio=statement['ebitdaratio'],
                operatingIncome=statement['operatingIncome'],
                operatingIncomeRatio=statement['operatingIncomeRatio'],
                totalOtherIncomeExpensesNet=statement['totalOtherIncomeExpensesNet'],
                incomeBeforeTax=statement['incomeBeforeTax'],
                incomeBeforeTaxRatio=statement['incomeBeforeTaxRatio'],
                incomeTaxExpense=statement['incomeTaxExpense'],
                netIncome=statement['netIncome'],
                netIncomeRatio=statement['netIncomeRatio'],
                eps=statement['eps'],
                epsdiluted=statement['epsdiluted'],
                weightedAverageShsOut=statement['weightedAverageShsOut'],
                weightedAverageShsOutDil=statement['weightedAverageShsOutDil']
            )
            income_statements.append(financial_statement)

        # Sort income statements by date (newest first)
        income_statements.sort(key=lambda x: x.date, reverse=True)

        # Update the stock object with new income statements
        if stock:
            stock.income_statement = income_statements
            stock.save()
        else:
            stock = Stock(symbol=symbol, income_statement=income_statements)
            stock.save()

        logging.info(f"Successfully fetched and saved income statement data for {symbol}")
        return income_statements

    except requests.RequestException as e:
        logging.error(f"Error fetching income statement data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching income statement data for {symbol}: {str(e)}")
        return None
    
def fetch_balance_sheet(symbol, years=5, force_refresh=False):
    try:
        stock = Stock.objects(symbol=symbol).first()
        
        # Check if we already have recent balance sheets (e.g., less than 1 day old)
        if not force_refresh and stock and stock.balance_sheets:
            latest_statement = stock.balance_sheets[0]
            if (datetime.now(timezone.utc) - latest_statement.date.replace(tzinfo=timezone.utc)).days < 1:
                logging.info(f"Using cached balance sheets for {symbol}")
                return stock.balance_sheets

        # If no recent data, fetch from FMP API
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        annual_url = f"{FMP_BASE_URL}/balance-sheet-statement/{symbol}?period=annual&limit={years}&apikey={FMP_API_KEY}"
        quarterly_url = f"{FMP_BASE_URL}/balance-sheet-statement/{symbol}?period=quarter&limit={years * 4}&apikey={FMP_API_KEY}"

        annual_response = requests.get(annual_url)
        annual_response.raise_for_status()
        annual_data = annual_response.json()

        try:
            quarterly_response = requests.get(quarterly_url)
            quarterly_response.raise_for_status()
            quarterly_data = quarterly_response.json()
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch quarterly data for {symbol}: {str(e)}")
            quarterly_data = []

        if not annual_data and not quarterly_data:
            logging.warning(f"No balance sheet data found for {symbol}")
            return None

        balance_sheets = []
        
        for statement in annual_data + quarterly_data:
            statement_date = datetime.strptime(statement['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if statement_date < start_date:
                continue
            
            balance_sheet = BalanceSheet(
                date=statement_date,
                symbol=statement['symbol'],
                reportedCurrency=statement['reportedCurrency'],
                cik=statement['cik'],
                fillingDate=datetime.strptime(statement['fillingDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc),
                acceptedDate=datetime.strptime(statement['acceptedDate'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc),
                calendarYear=statement['calendarYear'],
                period=statement['period'],
                cashAndCashEquivalents=statement['cashAndCashEquivalents'],
                shortTermInvestments=statement['shortTermInvestments'],
                cashAndShortTermInvestments=statement['cashAndShortTermInvestments'],
                netReceivables=statement['netReceivables'],
                inventory=statement['inventory'],
                otherCurrentAssets=statement['otherCurrentAssets'],
                totalCurrentAssets=statement['totalCurrentAssets'],
                propertyPlantEquipmentNet=statement['propertyPlantEquipmentNet'],
                goodwill=statement['goodwill'],
                intangibleAssets=statement['intangibleAssets'],
                goodwillAndIntangibleAssets=statement['goodwillAndIntangibleAssets'],
                longTermInvestments=statement['longTermInvestments'],
                taxAssets=statement['taxAssets'],
                otherNonCurrentAssets=statement['otherNonCurrentAssets'],
                totalNonCurrentAssets=statement['totalNonCurrentAssets'],
                otherAssets=statement['otherAssets'],
                totalAssets=statement['totalAssets'],
                accountPayables=statement['accountPayables'],
                shortTermDebt=statement['shortTermDebt'],
                taxPayables=statement['taxPayables'],
                deferredRevenue=statement['deferredRevenue'],
                otherCurrentLiabilities=statement['otherCurrentLiabilities'],
                totalCurrentLiabilities=statement['totalCurrentLiabilities'],
                longTermDebt=statement['longTermDebt'],
                deferredRevenueNonCurrent=statement['deferredRevenueNonCurrent'],
                deferredTaxLiabilitiesNonCurrent=statement['deferredTaxLiabilitiesNonCurrent'],
                otherNonCurrentLiabilities=statement['otherNonCurrentLiabilities'],
                totalNonCurrentLiabilities=statement['totalNonCurrentLiabilities'],
                otherLiabilities=statement['otherLiabilities'],
                capitalLeaseObligations=statement['capitalLeaseObligations'],
                totalLiabilities=statement['totalLiabilities'],
                preferredStock=statement['preferredStock'],
                commonStock=statement['commonStock'],
                retainedEarnings=statement['retainedEarnings'],
                accumulatedOtherComprehensiveIncomeLoss=statement['accumulatedOtherComprehensiveIncomeLoss'],
                othertotalStockholdersEquity=statement['othertotalStockholdersEquity'],
                totalStockholdersEquity=statement['totalStockholdersEquity'],
                totalLiabilitiesAndStockholdersEquity=statement['totalLiabilitiesAndStockholdersEquity'],
                minorityInterest=statement['minorityInterest'],
                totalEquity=statement['totalEquity'],
                totalLiabilitiesAndTotalEquity=statement['totalLiabilitiesAndTotalEquity'],
                totalInvestments=statement['totalInvestments'],
                totalDebt=statement['totalDebt'],
                netDebt=statement['netDebt']
            )
            balance_sheets.append(balance_sheet)

        # Sort balance sheets by date (newest first)
        balance_sheets.sort(key=lambda x: x.date, reverse=True)

        # Update the stock object with new balance sheets
        if stock:
            stock.balance_sheets = balance_sheets
            stock.save()
        else:
            stock = Stock(symbol=symbol, balance_sheets=balance_sheets)
            stock.save()

        logging.info(f"Successfully fetched and saved balance sheet data for {symbol}")
        return balance_sheets

    except requests.RequestException as e:
        logging.error(f"Error fetching balance sheet data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching balance sheet data for {symbol}: {str(e)}")
        return None
    
def fetch_cash_flow_statement(symbol):
    try:
        stock = Stock.objects(symbol=symbol).first()
        
        # Check if we already have a recent cash flow statement (e.g., less than 3 months old)
        if stock and stock.cash_flow_statements:
            latest_cash_flow = stock.cash_flow_statements[0]
            if (datetime.now(timezone.utc) - latest_cash_flow.date).days < 90:
                logging.info(f"Using cached cash flow statement for {symbol}")
                return stock.cash_flow_statements

        # If no recent data, fetch from FMP API
        url = f"{FMP_BASE_URL}/cash-flow-statement/{symbol}?period=annual&apikey={FMP_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data:
            logging.warning(f"No cash flow statement data found for {symbol}")
            return None

        cash_flow_statements = []
        for statement in data:
            cash_flow = CashFlowStatement(
                date=datetime.strptime(statement['date'], '%Y-%m-%d'),
                symbol=statement['symbol'],
                reportedCurrency=statement['reportedCurrency'],
                cik=statement['cik'],
                fillingDate=datetime.strptime(statement['fillingDate'], '%Y-%m-%d'),
                acceptedDate=datetime.strptime(statement['acceptedDate'], '%Y-%m-%d %H:%M:%S'),
                calendarYear=statement['calendarYear'],
                period=statement['period'],
                netIncome=statement['netIncome'],
                depreciationAndAmortization=statement['depreciationAndAmortization'],
                deferredIncomeTax=statement['deferredIncomeTax'],
                stockBasedCompensation=statement['stockBasedCompensation'],
                changeInWorkingCapital=statement['changeInWorkingCapital'],
                accountsReceivables=statement['accountsReceivables'],
                inventory=statement['inventory'],
                accountsPayables=statement['accountsPayables'],
                otherWorkingCapital=statement['otherWorkingCapital'],
                otherNonCashItems=statement['otherNonCashItems'],
                netCashProvidedByOperatingActivities=statement['netCashProvidedByOperatingActivities'],
                investmentsInPropertyPlantAndEquipment=statement['investmentsInPropertyPlantAndEquipment'],
                acquisitionsNet=statement['acquisitionsNet'],
                purchasesOfInvestments=statement['purchasesOfInvestments'],
                salesMaturitiesOfInvestments=statement['salesMaturitiesOfInvestments'],
                otherInvestingActivites=statement['otherInvestingActivites'],
                netCashUsedForInvestingActivites=statement['netCashUsedForInvestingActivites'],
                debtRepayment=statement['debtRepayment'],
                commonStockIssued=statement['commonStockIssued'],
                commonStockRepurchased=statement['commonStockRepurchased'],
                dividendsPaid=statement['dividendsPaid'],
                otherFinancingActivites=statement['otherFinancingActivites'],
                netCashUsedProvidedByFinancingActivities=statement['netCashUsedProvidedByFinancingActivities'],
                effectOfForexChangesOnCash=statement['effectOfForexChangesOnCash'],
                netChangeInCash=statement['netChangeInCash'],
                cashAtEndOfPeriod=statement['cashAtEndOfPeriod'],
                cashAtBeginningOfPeriod=statement['cashAtBeginningOfPeriod'],
                operatingCashFlow=statement['operatingCashFlow'],
                capitalExpenditure=statement['capitalExpenditure'],
                freeCashFlow=statement['freeCashFlow']
            )
            cash_flow_statements.append(cash_flow)

        logging.info(f"Successfully fetched cash flow statement data for {symbol}")
        return cash_flow_statements

    except requests.RequestException as e:
        logging.error(f"Error fetching cash flow statement data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching cash flow statement data for {symbol}: {str(e)}")
        return None
    
def fetch_financial_metrics(symbol):
    try:
        url = f"{FMP_BASE_URL}/key-metrics/{symbol}?period=annual&apikey={FMP_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data:
            logging.warning(f"No financial metrics data found for {symbol}")
            return None

        financial_metrics = []
        for metrics in data:
            financial_metric = FinancialMetrics(
                date=datetime.strptime(metrics['date'], '%Y-%m-%d'),
                calendarYear=metrics['calendarYear'],
                period=metrics['period'],
                revenuePerShare=metrics['revenuePerShare'],
                netIncomePerShare=metrics['netIncomePerShare'],
                operatingCashFlowPerShare=metrics['operatingCashFlowPerShare'],
                freeCashFlowPerShare=metrics['freeCashFlowPerShare'],
                cashPerShare=metrics['cashPerShare'],
                bookValuePerShare=metrics['bookValuePerShare'],
                tangibleBookValuePerShare=metrics['tangibleBookValuePerShare'],
                shareholdersEquityPerShare=metrics['shareholdersEquityPerShare'],
                interestDebtPerShare=metrics['interestDebtPerShare'],
                marketCap=metrics['marketCap'],
                enterpriseValue=metrics['enterpriseValue'],
                peRatio=metrics['peRatio'],
                priceToSalesRatio=metrics['priceToSalesRatio'],
                pocfratio=metrics['pocfratio'],
                pfcfRatio=metrics['pfcfRatio'],
                pbRatio=metrics['pbRatio'],
                ptbRatio=metrics['ptbRatio'],
                evToSales=metrics['evToSales'],
                enterpriseValueOverEBITDA=metrics['enterpriseValueOverEBITDA'],
                evToOperatingCashFlow=metrics['evToOperatingCashFlow'],
                evToFreeCashFlow=metrics['evToFreeCashFlow'],
                earningsYield=metrics['earningsYield'],
                freeCashFlowYield=metrics['freeCashFlowYield'],
                debtToEquity=metrics['debtToEquity'],
                debtToAssets=metrics['debtToAssets'],
                netDebtToEBITDA=metrics['netDebtToEBITDA'],
                currentRatio=metrics['currentRatio'],
                interestCoverage=metrics['interestCoverage'],
                incomeQuality=metrics['incomeQuality'],
                dividendYield=metrics['dividendYield'],
                payoutRatio=metrics['payoutRatio'],
                salesGeneralAndAdministrativeToRevenue=metrics['salesGeneralAndAdministrativeToRevenue'],
                researchAndDdevelopementToRevenue=metrics['researchAndDdevelopementToRevenue'],
                intangiblesToTotalAssets=metrics['intangiblesToTotalAssets'],
                capexToOperatingCashFlow=metrics['capexToOperatingCashFlow'],
                capexToRevenue=metrics['capexToRevenue'],
                capexToDepreciation=metrics['capexToDepreciation'],
                stockBasedCompensationToRevenue=metrics['stockBasedCompensationToRevenue'],
                grahamNumber=metrics['grahamNumber'],
                roic=metrics['roic'],
                returnOnTangibleAssets=metrics['returnOnTangibleAssets'],
                grahamNetNet=metrics['grahamNetNet'],
                workingCapital=metrics['workingCapital'],
                tangibleAssetValue=metrics['tangibleAssetValue'],
                netCurrentAssetValue=metrics['netCurrentAssetValue'],
                investedCapital=metrics['investedCapital'],
                averageReceivables=metrics['averageReceivables'],
                averagePayables=metrics['averagePayables'],
                averageInventory=metrics['averageInventory'],
                daysSalesOutstanding=metrics['daysSalesOutstanding'],
                daysPayablesOutstanding=metrics['daysPayablesOutstanding'],
                daysOfInventoryOnHand=metrics['daysOfInventoryOnHand'],
                receivablesTurnover=metrics['receivablesTurnover'],
                payablesTurnover=metrics['payablesTurnover'],
                inventoryTurnover=metrics['inventoryTurnover'],
                roe=metrics['roe'],
                capexPerShare=metrics['capexPerShare']
            )
            financial_metrics.append(financial_metric)

        logging.info(f"Successfully fetched financial metrics data for {symbol}")
        return financial_metrics

    except requests.RequestException as e:
        logging.error(f"Error fetching financial metrics data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching financial metrics data for {symbol}: {str(e)}")
        return None