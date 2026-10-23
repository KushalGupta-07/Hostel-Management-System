import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "hms-secret-key-hostal-2026")
    
    # MySQL Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "kushalgupta@27")
    DB_NAME = os.getenv("DB_NAME", "hostal_management")
    
    # App Settings
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
