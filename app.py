import logging
import os
import socket

from flask import Flask
from nacos import NacosClient
from selenium.webdriver.remote.remote_connection import RemoteConnection

from config import get_config, get_log_file_handler, get_log_stream_handler

app = Flask(__name__)
log_dir = "logs"
RemoteConnection.set_timeout(10)

def create_app():
    app.config.from_object(get_config())

    # 配置日誌
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    app.logger.addHandler(get_log_file_handler(log_dir))
    app.logger.setLevel(logging.INFO)
    app.logger.info('python-service startup')

    # 初始化 Nacos 客户端
    nacos_client = NacosClient(os.getenv('NACOS_SERVER_ADDR'), namespace=os.getenv('NACOS_NAMESPACE'))
    host = socket.gethostbyname(socket.gethostname())
    port = int(os.environ.get("PORT", 5000))
    service_name = os.getenv('NACOS_SERVICE_NAME')
    nacos_client.add_naming_instance(
        service_name,
        host,
        port,
        heartbeat_interval=5
    )

    # 注册路由
    from router import job_route
    app.register_blueprint(job_route, url_prefix='/job')

    return app

if __name__ == '__main__':
    create_app().run()

