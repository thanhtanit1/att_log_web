import os

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER = os.getenv("DB_SERVER", "113.176.95.32,8089")
    DB_DATABASE = os.getenv("DB_DATABASE", "CJ_AGRI_ATT_2022")
    DB_UID = os.getenv("DB_UID", "livestock")
    DB_PWD = os.getenv("DB_PWD", "C1vina@2022@@!")
    PAGE_SIZE = int(os.getenv("PAGE_SIZE", "20"))
