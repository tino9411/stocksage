from mongoengine import Document, StringField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, FloatField, DictField
from datetime import datetime

class Preference(EmbeddedDocument):
    preferred_stocks = ListField(StringField())
    preferred_sectors = ListField(StringField())
    preferred_model = StringField()
    risk_tolerance = StringField()
    investment_horizon = StringField()
    preferred_analysis_factors = ListField(StringField())

class WatchlistItem(EmbeddedDocument):
    symbol = StringField(required=True)
    added_date = DateTimeField(default=datetime.utcnow)
    notes = StringField()

class AnalysisHistory(EmbeddedDocument):
    date = DateTimeField(default=datetime.utcnow)
    stock_symbol = StringField(required=True)
    model_used = StringField(required=True)
    summary = StringField(required=True)
    recommendation = StringField()
    confidence_score = FloatField()

class Portfolio(EmbeddedDocument):
    symbol = StringField(required=True)
    quantity = FloatField(required=True)
    average_buy_price = FloatField(required=True)
    current_value = FloatField()
    purchase_date = DateTimeField()

class User(Document):
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)  # Remember to hash passwords before storing
    created_at = DateTimeField(default=datetime.utcnow)
    last_login = DateTimeField()
    preferences = EmbeddedDocumentField(Preference)
    watchlist = ListField(EmbeddedDocumentField(WatchlistItem))
    analysis_history = ListField(EmbeddedDocumentField(AnalysisHistory))
    portfolio = ListField(EmbeddedDocumentField(Portfolio))
    risk_profile = DictField()
    interaction_history = ListField(DictField())  # Store user interactions for personalization

    meta = {
        'indexes': [
            'username',
            'email',
            'preferences.preferred_stocks',
            'preferences.preferred_sectors'
        ]
    }