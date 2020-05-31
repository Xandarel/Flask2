import os


class Config:
    DB_CONNECTION = os.getenv('DB_CONNECTION', 'example_2.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret').encode()
