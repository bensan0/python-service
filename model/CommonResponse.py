from dataclasses import dataclass
from enum import Enum
from typing import Any

class StatusCode(Enum):
    OK = ("200", "成功")
    BAD_REQUEST = ("400", "错误的请求")
    NOT_FOUND = ("404", "未找到")
    INTERNAL_ERROR = ("500", "服务器内部错误")

    def __init__(self, code, message):
        self.code = code
        self.message = message

@dataclass
class CommonResponse:
    code: str = StatusCode.OK.code
    msg: str = ""
    data: Any = None

    def __init__(self, code: StatusCode, data: Any = None, msg: str = ""):
        self.code = code.code
        self.msg = msg
        self.data = data

    @classmethod
    def ok(cls, data=None):
        return cls(StatusCode.OK, data, StatusCode.OK.message)

    @classmethod
    def error(cls, status_code: StatusCode = StatusCode.INTERNAL_ERROR, data=None, msg: str = ""):
        return cls(status_code, data, status_code.message if len(msg) == 0 else msg)

    @classmethod
    def gen_response(cls, status_code: StatusCode, data = None, msg:str = ""):
        return cls(status_code, data, msg)