import os
from dotenv import load_dotenv
env_file = f".env.{os.getenv('FLASK_ENV', 'dev')}"
load_dotenv(env_file)

class Config:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}{('/' + os.getenv('MYSQL_DB')) if os.getenv('MYSQL_DB') is not None else ''}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevConfig(Config):
    DEBUG = True

class ProdConfig(Config):
    DEBUG = False

config = {
    'dev': DevConfig,
    'prod': ProdConfig
}

def get_config():
    return config[os.getenv('FLASK_ENV', 'dev')]