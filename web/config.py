import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-super-secret-key')

    # Database configuration
    DB_HOST = os.environ.get('DB_HOST')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USER = os.environ.get('DB_USER')
    DB_PASS = os.environ.get('DB_PASS') # Will be None in Azure
    DB_PORT = os.environ.get('DB_PORT', '5432')

    # Determine if running in Azure based on Managed Identity presence
    # The AZURE_CLIENT_ID is automatically injected into the Container App env
    IS_AZURE = 'AZURE_CLIENT_ID' in os.environ

    # Construct the database URI
    if IS_AZURE:
        # Use Azure AD authentication (passwordless)
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        # Use password for local development
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False