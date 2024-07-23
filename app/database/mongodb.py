from mongoengine import connect
from mongoengine.connection import get_db
from dotenv import load_dotenv
import os
import logging

load_dotenv()

def initialize_db():
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is not set")
    
    # Extract the database name from the connection string or use a default
    db_name = os.getenv('DB_NAME', 'stocksage')
    
    try:
        # Connect to MongoDB with the specific database name
        connect(db=db_name, host=mongodb_uri)
        
        # Verify connection by getting the database
        db = get_db()
        logging.info(f"Successfully connected to MongoDB. Database name: {db.name}")
        
        # List all collections
        collections = db.list_collection_names()
        logging.info(f"Existing collections: {collections}")
        
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

# Call this function when your application starts
if __name__ == "__main__":
    initialize_db()