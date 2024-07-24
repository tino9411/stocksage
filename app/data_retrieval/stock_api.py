from app.models.stock import Stock, HistoricalData, FinancialStatement, BalanceSheet, CashFlowStatement, KeyMetrics, RealTimeQuote
from datetime import datetime, timezone, timedelta
import logging
import requests
import os
from dotenv import load_dotenv
from mongoengine.errors import ValidationError
import yfinance as yf

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

def fetch_stock_data(symbol):
    try:
        # Fetch company profile from FMP
        profile_url = f"{FMP_BASE_URL}/profile/{symbol}?apikey={FMP_API_KEY}"
        profile_response = requests.get(profile_url)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        if not profile_data:
            logging.warning(f"No profile data found for symbol {symbol}")
            return None

        company_data = profile_data[0]  # The API returns a list with one item

        # Fetch real-time quote
        real_time_quote = fetch_real_time_quote(symbol)

        # Fetch historical data from yfinance
        yf_stock = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        hist = yf_stock.history(start=start_date, end=end_date)

        stock = Stock.objects(symbol=symbol).first()
        if not stock:
            stock = Stock(symbol=symbol)

        # Update fields from company profile
        for key, value in company_data.items():
            if hasattr(stock, key):
                setattr(stock, key, value)

        # Update real-time quote
        if real_time_quote:
            stock.real_time_quote = real_time_quote
        else:
            logging.warning(f"No real-time quote data available for {symbol}")

        # Update historical data
        stock.historical_data = [
            HistoricalData(
                date=date.to_pydatetime().replace(tzinfo=timezone.utc),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume'])
            ) for date, row in hist.iterrows()
        ]

        # Fetch key metrics (both annual and quarterly)
        key_metrics = fetch_key_metrics(symbol)
        if key_metrics:
            stock.key_metrics = key_metrics
        else:
            logging.warning(f"No key metrics data available for {symbol}")

        stock.last_updated = datetime.now(timezone.utc)

        try:
            stock.save()
            logging.info(f"Successfully saved data for {symbol}")
        except ValidationError as ve:
            logging.error(f"Validation error when saving data for {symbol}: {str(ve)}")
            return None

        logging.info(f"Successfully updated data for {symbol}")
        return stock

    except requests.RequestException as e:
        logging.error(f"Error fetching data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching data for {symbol}: {str(e)}", exc_info=True)
        return None

def fetch_real_time_quote(symbol):
    try:
        url = f"{FMP_BASE_URL}/quote/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        logging.debug(f"Raw real-time quote data for {symbol}: {data}")

        if not data:
            logging.warning(f"Empty response when fetching real-time quote for {symbol}")
            return None

        quote_data = data[0]  # The API returns a list with one item

        # Function to safely convert to float
        def safe_float(value):
            try:
                return float(value) if value is not None else None
            except ValueError:
                logging.warning(f"Could not convert {value} to float")
                return None

        # Function to safely convert to int
        def safe_int(value):
            try:
                return int(value) if value is not None else None
            except ValueError:
                logging.warning(f"Could not convert {value} to int")
                return None

        # Function to safely parse datetime
        def safe_datetime(value):
            if value is None:
                return None
            try:
                if isinstance(value, str):
                    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%f%z')
                elif isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            except ValueError as e:
                logging.warning(f"Could not parse datetime {value}: {e}")
            return None

        return RealTimeQuote(
            price=safe_float(quote_data.get('price')),
            changesPercentage=safe_float(quote_data.get('changesPercentage')),
            change=safe_float(quote_data.get('change')),
            dayLow=safe_float(quote_data.get('dayLow')),
            dayHigh=safe_float(quote_data.get('dayHigh')),
            yearHigh=safe_float(quote_data.get('yearHigh')),
            yearLow=safe_float(quote_data.get('yearLow')),
            marketCap=safe_float(quote_data.get('marketCap')),
            priceAvg50=safe_float(quote_data.get('priceAvg50')),
            priceAvg200=safe_float(quote_data.get('priceAvg200')),
            volume=safe_int(quote_data.get('volume')),
            avgVolume=safe_int(quote_data.get('avgVolume')),
            open=safe_float(quote_data.get('open')),
            previousClose=safe_float(quote_data.get('previousClose')),
            eps=safe_float(quote_data.get('eps')),
            pe=safe_float(quote_data.get('pe')),
            earningsAnnouncement=safe_datetime(quote_data.get('earningsAnnouncement')),
            sharesOutstanding=safe_float(quote_data.get('sharesOutstanding')),
            timestamp=safe_datetime(quote_data.get('timestamp'))
        )

    except requests.RequestException as e:
        logging.error(f"Request exception when fetching real-time quote for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching real-time quote for {symbol}: {str(e)}", exc_info=True)
        return None
        
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
    
def fetch_cash_flow_statement(symbol, years=5, force_refresh=False):
    try:
        stock = Stock.objects(symbol=symbol).first()
        
        # Check if we already have recent cash flow statements (e.g., less than 1 day old)
        if not force_refresh and stock and stock.cash_flow_statements:
            latest_statement = stock.cash_flow_statements[0]
            if (datetime.now(timezone.utc) - latest_statement.date.replace(tzinfo=timezone.utc)).days < 1:
                logging.info(f"Using cached cash flow statements for {symbol}")
                return stock.cash_flow_statements

        # If no recent data, fetch from FMP API
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        annual_url = f"{FMP_BASE_URL}/cash-flow-statement/{symbol}?period=annual&limit={years}&apikey={FMP_API_KEY}"
        quarterly_url = f"{FMP_BASE_URL}/cash-flow-statement/{symbol}?period=quarter&limit={years * 4}&apikey={FMP_API_KEY}"

        annual_response = requests.get(annual_url)
        annual_response.raise_for_status()
        annual_data = annual_response.json()

        try:
            quarterly_response = requests.get(quarterly_url)
            quarterly_response.raise_for_status()
            quarterly_data = quarterly_response.json()
        except requests.RequestException as e:
            logging.warning(f"Failed to fetch quarterly cash flow data for {symbol}: {str(e)}")
            quarterly_data = []

        if not annual_data and not quarterly_data:
            logging.warning(f"No cash flow statement data found for {symbol}")
            return None

        cash_flow_statements = []
        
        for statement in annual_data + quarterly_data:
            statement_date = datetime.strptime(statement['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if statement_date < start_date:
                continue
            
            cash_flow = CashFlowStatement(
                date=statement_date,
                symbol=statement['symbol'],
                reportedCurrency=statement['reportedCurrency'],
                cik=statement['cik'],
                fillingDate=datetime.strptime(statement['fillingDate'], '%Y-%m-%d').replace(tzinfo=timezone.utc),
                acceptedDate=datetime.strptime(statement['acceptedDate'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc),
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

        # Sort cash flow statements by date (newest first)
        cash_flow_statements.sort(key=lambda x: x.date, reverse=True)

        # Update the stock object with new cash flow statements
        if stock:
            stock.cash_flow_statements = cash_flow_statements
            stock.save()
        else:
            stock = Stock(symbol=symbol, cash_flow_statements=cash_flow_statements)
            stock.save()

        logging.info(f"Successfully fetched and saved cash flow statement data for {symbol}")
        return cash_flow_statements

    except requests.RequestException as e:
        logging.error(f"Error fetching cash flow statement data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching cash flow statement data for {symbol}: {str(e)}")
        return None
    
def fetch_key_metrics(symbol, years=5):
    try:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=years * 365)
        
        # Fetch both annual and quarterly data
        annual_url = f"{FMP_BASE_URL}/key-metrics/{symbol}?period=annual&limit={years}&apikey={FMP_API_KEY}"
        quarterly_url = f"{FMP_BASE_URL}/key-metrics/{symbol}?period=quarter&limit={years * 4}&apikey={FMP_API_KEY}"

        annual_response = requests.get(annual_url)
        annual_response.raise_for_status()
        annual_data = annual_response.json()

        quarterly_response = requests.get(quarterly_url)
        quarterly_response.raise_for_status()
        quarterly_data = quarterly_response.json()

        all_metrics = annual_data + quarterly_data

        if not all_metrics:
            logging.warning(f"No key metrics data found for {symbol}")
            return None

        key_metrics = []
        
        for metrics in all_metrics:
            metrics_date = datetime.strptime(metrics['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if metrics_date < start_date:
                continue
            
            key_metric = KeyMetrics(
                date=metrics_date,
                period=metrics['period'],  # Use the period from the API response
                symbol=symbol,
                revenuePerShare=metrics.get('revenuePerShare'),
                netIncomePerShare=metrics.get('netIncomePerShare'),
                operatingCashFlowPerShare=metrics.get('operatingCashFlowPerShare'),
                freeCashFlowPerShare=metrics.get('freeCashFlowPerShare'),
                cashPerShare=metrics.get('cashPerShare'),
                bookValuePerShare=metrics.get('bookValuePerShare'),
                tangibleBookValuePerShare=metrics.get('tangibleBookValuePerShare'),
                shareholdersEquityPerShare=metrics.get('shareholdersEquityPerShare'),
                interestDebtPerShare=metrics.get('interestDebtPerShare'),
                marketCap=metrics.get('marketCap'),
                enterpriseValue=metrics.get('enterpriseValue'),
                peRatio=metrics.get('peRatio'),
                priceToSalesRatio=metrics.get('priceToSalesRatio'),
                pocfratio=metrics.get('pocfratio'),
                pfcfRatio=metrics.get('pfcfRatio'),
                pbRatio=metrics.get('pbRatio'),
                ptbRatio=metrics.get('ptbRatio'),
                evToSales=metrics.get('evToSales'),
                enterpriseValueOverEBITDA=metrics.get('enterpriseValueOverEBITDA'),
                evToOperatingCashFlow=metrics.get('evToOperatingCashFlow'),
                evToFreeCashFlow=metrics.get('evToFreeCashFlow'),
                earningsYield=metrics.get('earningsYield'),
                freeCashFlowYield=metrics.get('freeCashFlowYield'),
                debtToEquity=metrics.get('debtToEquity'),
                debtToAssets=metrics.get('debtToAssets'),
                netDebtToEBITDA=metrics.get('netDebtToEBITDA'),
                currentRatio=metrics.get('currentRatio'),
                interestCoverage=metrics.get('interestCoverage'),
                incomeQuality=metrics.get('incomeQuality'),
                dividendYield=metrics.get('dividendYield'),
                payoutRatio=metrics.get('payoutRatio'),
                salesGeneralAndAdministrativeToRevenue=metrics.get('salesGeneralAndAdministrativeToRevenue'),
                researchAndDevelopmentToRevenue=metrics.get('researchAndDevelopementToRevenue'),
                intangiblesToTotalAssets=metrics.get('intangiblesToTotalAssets'),
                capexToOperatingCashFlow=metrics.get('capexToOperatingCashFlow'),
                capexToRevenue=metrics.get('capexToRevenue'),
                capexToDepreciation=metrics.get('capexToDepreciation'),
                stockBasedCompensationToRevenue=metrics.get('stockBasedCompensationToRevenue'),
                grahamNumber=metrics.get('grahamNumber'),
                roic=metrics.get('roic'),
                returnOnTangibleAssets=metrics.get('returnOnTangibleAssets'),
                grahamNetNet=metrics.get('grahamNetNet'),
                workingCapital=metrics.get('workingCapital'),
                tangibleAssetValue=metrics.get('tangibleAssetValue'),
                netCurrentAssetValue=metrics.get('netCurrentAssetValue'),
                investedCapital=metrics.get('investedCapital'),
                averageReceivables=metrics.get('averageReceivables'),
                averagePayables=metrics.get('averagePayables'),
                averageInventory=metrics.get('averageInventory'),
                daysSalesOutstanding=metrics.get('daysSalesOutstanding'),
                daysPayablesOutstanding=metrics.get('daysPayablesOutstanding'),
                daysOfInventoryOnHand=metrics.get('daysOfInventoryOnHand'),
                receivablesTurnover=metrics.get('receivablesTurnover'),
                payablesTurnover=metrics.get('payablesTurnover'),
                inventoryTurnover=metrics.get('inventoryTurnover'),
                roe=metrics.get('roe'),
                capexPerShare=metrics.get('capexPerShare')
            )
            key_metrics.append(key_metric)

        # Sort key metrics by date (newest first)
        key_metrics.sort(key=lambda x: x.date, reverse=True)

        return key_metrics

    except requests.RequestException as e:
        logging.error(f"Error fetching key metrics data for {symbol}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching key metrics data for {symbol}: {str(e)}")
        return None