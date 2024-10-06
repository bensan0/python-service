import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


def get_log_file_handler(log_dir_path:str):
    log_file_name = log_dir_path + os.sep + datetime.now().strftime("%Y%m%d") + ".log"
    file_handler = RotatingFileHandler(
        log_file_name,
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(get_log_formatter())
    file_handler.setLevel(logging.INFO)
    return file_handler

def get_log_stream_handler():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(get_log_formatter())
    console_handler.setLevel(logging.INFO)
    return console_handler

def get_log_formatter():
    return logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )