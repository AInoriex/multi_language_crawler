import requests
from time import sleep
from random import randint
from os import getenv
from utils.logger import logger
from utils.config import Config

# class LarkNotice():
#     def __init__(self, notice_text) -> None:
#         self.notice_text = notice_text

def alarm_lark_text(webhook:str, text:str, retry:int=3):
    """
    飞书机器人告警

    :param webhook string: 飞书机器人webhook
    :param text string: 告警信息
    :param retry int: 重新尝试发送的次数
    :return: None
    """
    # Expamle Json Send
    # {
	#     "msg_type": "text",
	#     "content": {"text": "test hello world."}
    # }
    try:
        params = {
            "msg_type": "text",
            "content": {"text": f"{text}"}
        }
        # print(f"request: {webhook} | {params}")
        resp = requests.post(url=webhook, json=params)
        # print(f"response: {resp.status_code} {resp.content}")
        assert resp.status_code == 200
        assert resp.json()["code"] == 0
    except Exception as e:
        logger.error(f"Lark > [!] 发送飞书失败: {e}")
        if retry > 0:
            sleep(randint(3,5))
            return alarm_lark_text(webhook=webhook, text=text, retry=retry-1)
        else:
            # raise e
            return
    else:
        logger.debug(f"Lark > 已通知飞书: {webhook}")

def alarm(level:str, text:str):
    level = level.lower()
    if level == "debug":
        alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_DEBUG"), text=text)
    elif level == "warning":
        alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_INFO"), text=text)
    elif level == "error":
        alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_ERROR"), text=text)
    else:
        alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_INFO"), text=text)
