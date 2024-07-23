from mongoengine import Document, StringField, DateTimeField, FloatField, IntField, EmbeddedDocument, EmbeddedDocumentField, ListField, DictField
from datetime import datetime, timezone

class HistoricalData(EmbeddedDocument):
    date = DateTimeField(required=True)
    open = FloatField(required=True)
    high = FloatField(required=True)
    low = FloatField(required=True)
    close = FloatField(required=True)
    volume = IntField(required=True)

class Stock(Document):
    symbol = StringField(required=True, unique=True)
    company_name = StringField()
    sector = StringField()
    industry = StringField()
    last_updated = DateTimeField(default=lambda: datetime.now(timezone.utc))
    current_data = DictField()
    historical_data = ListField(EmbeddedDocumentField(HistoricalData))
    financial_ratios = DictField()

    meta = {
        'indexes': [
            'symbol',
            ('symbol', '-last_updated'),
            'sector',
            'industry',
            'last_updated'
        ]
    }