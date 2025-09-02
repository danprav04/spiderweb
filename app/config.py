# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SYNC_DATABASE_URL = os.environ.get("SYNC_DATABASE_URL")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_HOURS = int(os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS"))
    ALGORITHM = os.environ.get('ALGORITHM')
    TESTING_DEVICE = os.environ.get('TESTING_DEVICE')
    PORT = os.environ.get('PORT')
