import dataclasses
import traceback
import uuid

from flask import Blueprint, jsonify, request

import app
import service
from model import CommonResponse

job_route = Blueprint('job', __name__)

@job_route.route('/crawl_tx', methods=["GET"])
def crawl_tx():
    try:
        data = service.crawl_tx()
        return jsonify(dataclasses.asdict(CommonResponse.ok(data)))
    except Exception as e:
        trace = uuid.uuid1().hex
        app.app.logger.error(f"trace-code: {trace} \n 爬蟲台指期發生錯誤: {repr(e)}\n {traceback.format_exc()}")
        return jsonify(dataclasses.asdict(CommonResponse.error(msg=trace)))

@job_route.route('/craw_america_tx', methods=["GET"])
def craw_america_tx():
    try:
        data = service.crawl_america_tx()
        return jsonify(dataclasses.asdict(CommonResponse.ok(data)))
    except Exception as e:
        trace = uuid.uuid1().hex
        app.app.logger.error(f"trace-code: {trace} \n 爬蟲美股指數發生錯誤: {repr(e)}\n {traceback.format_exc()}")
        return jsonify(dataclasses.asdict(CommonResponse.error(msg=trace)))

@job_route.route("/craw_realtime", methods=["GET"])
def craw_realtime():
    try:
        data = service.craw_yahoo_realtime()
        return jsonify(dataclasses.asdict(CommonResponse.ok(data)))
    except Exception as e:
        trace = uuid.uuid1().hex
        app.app.logger.error(f"trace-code: {trace} \n 爬蟲yahoo即時發生錯誤: {repr(e)}\n {traceback.format_exc()}")
        return jsonify(dataclasses.asdict(CommonResponse.error(msg=trace)))

@job_route.route("/crawl_routine", methods=["GET"])
def crawl_routine():
    try:
        twse = service.crawl_twse()
        tpex = service.crawl_tpex()
        return jsonify(dataclasses.asdict(CommonResponse.ok(twse + tpex)))
    except Exception as e:
        trace = uuid.uuid1().hex
        app.app.logger.error(f"trace-code: {trace} \n 爬蟲routine發生錯誤: {repr(e)}\n {traceback.format_exc()}")
        return jsonify(dataclasses.asdict(CommonResponse.error(msg=trace)))

@job_route.route("/crawl_index", methods=["GET"])
def crawl_index():
    try:
        data = service.crawl_index()
        return jsonify(dataclasses.asdict(CommonResponse.ok(data)))
    except Exception as e:
        trace = uuid.uuid1().hex
        app.app.logger.error(f"trace-code: {trace} \n 爬蟲大盤發生錯誤: {repr(e)}\n {traceback.format_exc()}")
        return jsonify(dataclasses.asdict(CommonResponse.error(msg=trace)))