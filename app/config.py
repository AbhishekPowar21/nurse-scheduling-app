from datetime import timedelta

class Config:
    # MySQL database credentials
    MYSQL_HOST = 'localhost'  # Change this as needed
    MYSQL_DATABASE = 'nurse_scheduling'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'root'
    
    # Secret key for session management
    SECRET_KEY = 'a5890fb629a53a3481446d48e35276c0dbf8f29713ebaa51'  # Keep it unique and secret

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=20)  # Set session lifetime to 10 seconds
    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production if using HTTPS
