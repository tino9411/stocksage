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
class Stock(Document):
    symbol = StringField(required=True, unique=True)
    company_name = StringField()
    sector = StringField()
    industry = StringField()
    last_updated = DateTimeField(default=lambda: datetime.now(timezone.utc))
    current_data = DictField()
    historical_data = ListField(EmbeddedDocumentField(HistoricalData))
    financial_ratios = DictField()
    sec_reports = ListField(EmbeddedDocumentField(SECReport))
    income_statement = ListField(EmbeddedDocumentField(FinancialStatement))

    meta = {
        'indexes': [
            'symbol',
            ('symbol', '-last_updated'),
            'sector',
            'industry',
            'last_updated'
        ]
    }