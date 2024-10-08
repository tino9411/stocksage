from mongoengine import Document, StringField, DateTimeField, FloatField, IntField, EmbeddedDocument, EmbeddedDocumentField, ListField, DictField, BooleanField
from datetime import datetime, timezone

class HistoricalData(EmbeddedDocument):
    date = DateTimeField(required=True)
    open = FloatField(required=True)
    high = FloatField(required=True)
    low = FloatField(required=True)
    close = FloatField(required=True)
    volume = IntField(required=True)

class SECReport(EmbeddedDocument):
    filing_type = StringField(required=True)
    url = StringField(required=True)
    retrieved_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    full_text = StringField(required=True)
    full_text_length = IntField()
    truncated = BooleanField(default=False)

class FinancialStatement(EmbeddedDocument):
    date = DateTimeField(required=True)
    symbol = StringField(required=True)
    reportedCurrency = StringField()
    cik = StringField()
    fillingDate = DateTimeField()
    acceptedDate = DateTimeField()
    calendarYear = StringField()
    period = StringField()
    revenue = FloatField()
    costOfRevenue = FloatField()
    grossProfit = FloatField()
    grossProfitRatio = FloatField()
    researchAndDevelopmentExpenses = FloatField()
    generalAndAdministrativeExpenses = FloatField()
    sellingAndMarketingExpenses = FloatField()
    sellingGeneralAndAdministrativeExpenses = FloatField()
    otherExpenses = FloatField()
    operatingExpenses = FloatField()
    costAndExpenses = FloatField()
    interestIncome = FloatField()
    interestExpense = FloatField()
    depreciationAndAmortization = FloatField()
    ebitda = FloatField()
    ebitdaratio = FloatField()
    operatingIncome = FloatField()
    operatingIncomeRatio = FloatField()
    totalOtherIncomeExpensesNet = FloatField()
    incomeBeforeTax = FloatField()
    incomeBeforeTaxRatio = FloatField()
    incomeTaxExpense = FloatField()
    netIncome = FloatField()
    netIncomeRatio = FloatField()
    eps = FloatField()
    epsdiluted = FloatField()
    weightedAverageShsOut = FloatField()
    weightedAverageShsOutDil = FloatField()

class BalanceSheet(EmbeddedDocument):
    date = DateTimeField(required=True)
    symbol = StringField(required=True)
    reportedCurrency = StringField()
    cik = StringField()
    fillingDate = DateTimeField()
    acceptedDate = DateTimeField()
    calendarYear = StringField()
    period = StringField()
    cashAndCashEquivalents = FloatField()
    shortTermInvestments = FloatField()
    cashAndShortTermInvestments = FloatField()
    netReceivables = FloatField()
    inventory = FloatField()
    otherCurrentAssets = FloatField()
    totalCurrentAssets = FloatField()
    propertyPlantEquipmentNet = FloatField()
    goodwill = FloatField()
    intangibleAssets = FloatField()
    goodwillAndIntangibleAssets = FloatField()
    longTermInvestments = FloatField()
    taxAssets = FloatField()
    otherNonCurrentAssets = FloatField()
    totalNonCurrentAssets = FloatField()
    otherAssets = FloatField()
    totalAssets = FloatField()
    accountPayables = FloatField()
    shortTermDebt = FloatField()
    taxPayables = FloatField()
    deferredRevenue = FloatField()
    otherCurrentLiabilities = FloatField()
    totalCurrentLiabilities = FloatField()
    longTermDebt = FloatField()
    deferredRevenueNonCurrent = FloatField()
    deferredTaxLiabilitiesNonCurrent = FloatField()
    otherNonCurrentLiabilities = FloatField()
    totalNonCurrentLiabilities = FloatField()
    otherLiabilities = FloatField()
    capitalLeaseObligations = FloatField()
    totalLiabilities = FloatField()
    preferredStock = FloatField()
    commonStock = FloatField()
    retainedEarnings = FloatField()
    accumulatedOtherComprehensiveIncomeLoss = FloatField()
    othertotalStockholdersEquity = FloatField()
    totalStockholdersEquity = FloatField()
    totalLiabilitiesAndStockholdersEquity = FloatField()
    minorityInterest = FloatField()
    totalEquity = FloatField()
    totalLiabilitiesAndTotalEquity = FloatField()
    totalInvestments = FloatField()
    totalDebt = FloatField()
    netDebt = FloatField()

class CashFlowStatement(EmbeddedDocument):
    date = DateTimeField(required=True)
    symbol = StringField(required=True)
    reportedCurrency = StringField()
    cik = StringField()
    fillingDate = DateTimeField()
    acceptedDate = DateTimeField()
    calendarYear = StringField()
    period = StringField()
    netIncome = FloatField()
    depreciationAndAmortization = FloatField()
    deferredIncomeTax = FloatField()
    stockBasedCompensation = FloatField()
    changeInWorkingCapital = FloatField()
    accountsReceivables = FloatField()
    inventory = FloatField()
    accountsPayables = FloatField()
    otherWorkingCapital = FloatField()
    otherNonCashItems = FloatField()
    netCashProvidedByOperatingActivities = FloatField()
    investmentsInPropertyPlantAndEquipment = FloatField()
    acquisitionsNet = FloatField()
    purchasesOfInvestments = FloatField()
    salesMaturitiesOfInvestments = FloatField()
    otherInvestingActivites = FloatField()
    netCashUsedForInvestingActivites = FloatField()
    debtRepayment = FloatField()
    commonStockIssued = FloatField()
    commonStockRepurchased = FloatField()
    dividendsPaid = FloatField()
    otherFinancingActivites = FloatField()
    netCashUsedProvidedByFinancingActivities = FloatField()
    effectOfForexChangesOnCash = FloatField()
    netChangeInCash = FloatField()
    cashAtEndOfPeriod = FloatField()
    cashAtBeginningOfPeriod = FloatField()
    operatingCashFlow = FloatField()
    capitalExpenditure = FloatField()
    freeCashFlow = FloatField()

class KeyMetrics(EmbeddedDocument):
    date = DateTimeField(required=True)
    period = StringField(required=True)  # 'annual' or 'quarterly'
    symbol = StringField(required=True)
    revenuePerShare = FloatField()
    netIncomePerShare = FloatField()
    operatingCashFlowPerShare = FloatField()
    freeCashFlowPerShare = FloatField()
    cashPerShare = FloatField()
    bookValuePerShare = FloatField()
    tangibleBookValuePerShare = FloatField()
    shareholdersEquityPerShare = FloatField()
    interestDebtPerShare = FloatField()
    marketCap = FloatField()
    enterpriseValue = FloatField()
    peRatio = FloatField()
    priceToSalesRatio = FloatField()
    pocfratio = FloatField()
    pfcfRatio = FloatField()
    pbRatio = FloatField()
    ptbRatio = FloatField()
    evToSales = FloatField()
    enterpriseValueOverEBITDA = FloatField()
    evToOperatingCashFlow = FloatField()
    evToFreeCashFlow = FloatField()
    earningsYield = FloatField()
    freeCashFlowYield = FloatField()
    debtToEquity = FloatField()
    debtToAssets = FloatField()
    netDebtToEBITDA = FloatField()
    currentRatio = FloatField()
    interestCoverage = FloatField()
    incomeQuality = FloatField()
    dividendYield = FloatField()
    payoutRatio = FloatField()
    salesGeneralAndAdministrativeToRevenue = FloatField()
    researchAndDevelopmentToRevenue = FloatField()
    intangiblesToTotalAssets = FloatField()
    capexToOperatingCashFlow = FloatField()
    capexToRevenue = FloatField()
    capexToDepreciation = FloatField()
    stockBasedCompensationToRevenue = FloatField()
    grahamNumber = FloatField()
    roic = FloatField()
    returnOnTangibleAssets = FloatField()
    grahamNetNet = FloatField()
    workingCapital = FloatField()
    tangibleAssetValue = FloatField()
    netCurrentAssetValue = FloatField()
    investedCapital = FloatField()
    averageReceivables = FloatField()
    averagePayables = FloatField()
    averageInventory = FloatField()
    daysSalesOutstanding = FloatField()
    daysPayablesOutstanding = FloatField()
    daysOfInventoryOnHand = FloatField()
    receivablesTurnover = FloatField()
    payablesTurnover = FloatField()
    inventoryTurnover = FloatField()
    roe = FloatField()
    capexPerShare = FloatField()

class RealTimeQuote(EmbeddedDocument):
    price = FloatField(required=False)
    changesPercentage = FloatField(required=False)
    change = FloatField(required=False)
    dayLow = FloatField(required=False)
    dayHigh = FloatField(required=False)
    yearHigh = FloatField(required=False)
    yearLow = FloatField(required=False)
    marketCap = FloatField(required=False)
    priceAvg50 = FloatField(required=False)
    priceAvg200 = FloatField(required=False)
    volume = IntField(required=False)
    avgVolume = IntField(required=False)
    open = FloatField(required=False)
    previousClose = FloatField(required=False)
    eps = FloatField(required=False)
    pe = FloatField(required=False)
    earningsAnnouncement = DateTimeField(required=False)
    sharesOutstanding = FloatField(required=False)
    timestamp = DateTimeField(required=False)

class Stock(Document):
    symbol = StringField(required=True, unique=True)
    price = FloatField()
    beta = FloatField()
    volAvg = IntField()
    mktCap = FloatField()
    lastDiv = FloatField()
    range = StringField()
    changes = FloatField()
    companyName = StringField()
    currency = StringField()
    cik = StringField()
    isin = StringField()
    cusip = StringField()
    exchange = StringField()
    exchangeShortName = StringField()
    industry = StringField()
    website = StringField()
    description = StringField()
    ceo = StringField()
    sector = StringField()
    country = StringField()
    fullTimeEmployees = StringField()
    phone = StringField()
    address = StringField()
    city = StringField()
    state = StringField()
    zip = StringField()
    dcfDiff = FloatField()
    dcf = FloatField()
    image = StringField()
    ipoDate = StringField()
    defaultImage = BooleanField()
    isEtf = BooleanField()
    isActivelyTrading = BooleanField()
    isAdr = BooleanField()
    isFund = BooleanField()
    
    last_updated = DateTimeField(default=lambda: datetime.now(timezone.utc))
    historical_data = ListField(EmbeddedDocumentField('HistoricalData'))
    financial_ratios = DictField()
    sec_reports = ListField(EmbeddedDocumentField('SECReport'))
    income_statement = ListField(EmbeddedDocumentField('FinancialStatement'))
    balance_sheets = ListField(EmbeddedDocumentField('BalanceSheet'))
    cash_flow_statements = ListField(EmbeddedDocumentField('CashFlowStatement'))
    key_metrics = ListField(EmbeddedDocumentField('KeyMetrics'))
    real_time_quote = EmbeddedDocumentField(RealTimeQuote)

    meta = {
        'indexes': [
            'symbol',
            ('symbol', '-last_updated'),
            'sector',
            'industry',
            'last_updated'
        ]
    }