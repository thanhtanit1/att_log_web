import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER = os.getenv("DB_SERVER", "")
    DB_DATABASE = os.getenv("DB_DATABASE", "")
    DB_UID = os.getenv("DB_UID", "")
    DB_PWD = os.getenv("DB_PWD", "")
    DB_ENCRYPT = os.getenv("DB_ENCRYPT", "yes")
    DB_TRUST_CERT = os.getenv("DB_TRUST_CERT", "yes")
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "30"))
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "20"))
