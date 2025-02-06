# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

from uuid import uuid4
from sys import exit
from time import sleep
from os import getenv
from utils.utime import get_time_stamp
from utils.lark import alarm_lark_text, alarm
from utils.logger import logger
from utils.context import Context
from database.crawler_audio_download_info import request_create_audio_api
from handler.areena_podcastit import request_podcastit_list_api, request_podcastit_search_api, parse_podcastit_list_response
from model.areena_podcastit import format_areena_audio_object

SERVER_NAME = getenv("SERVER_NAME")
''' 服务名称 '''
LIMIT_FAIL_COUNT = int(getenv("LIMIT_FAIL_COUNT"))
''' 处理失败任务限制数 '''
    
def scrape_areena_podcastit_handler(ctx:Context, scrape_mode:str="", page:int=1, _page_size:int=16):
    if not scrape_mode or scrape_mode not in ["arrena_podcastit_list", "arrena_podcastit_search"]:
        raise ValueError("请指定scrape_areena_podcastit_handler scrape_mode采集模式（arrena_podcastit_list/arrena_podcastit_search）")
    if scrape_mode == "arrena_podcastit_list":
        # 请求播客列表接口
        response = request_podcastit_list_api(
            url="https://areena.api.yle.fi/v1/ui/content/list",
            page=page,
            page_size=_page_size,
            token=ctx.get("arrena_podcastit_list_token"),
        )
    elif scrape_mode == "arrena_podcastit_search":
        # 请求播客搜索接口
        if ctx.get("query") is None:
            raise ValueError("请指定scrape_areena_podcastit_handler搜索关键词")
        response = request_podcastit_search_api(
            url="https://areena.api.yle.fi/v1/ui/search",
            query=ctx.get("query"),
            page=page,
            page_size=_page_size,
        )
    for audio_url in parse_podcastit_list_response(response):
        logger.debug(f"scrape_areena_podcastit_handler > parse audio_url:{audio_url}")
        # 格式化数据
        audio_obj = format_areena_audio_object(
            task_id=ctx.get("task_id"),
            audio_url=audio_url,
            duration=0,
            language="fi",
            source_id="",
        )

        # 数据入库
        create_api = "%s?sign=%d" % (getenv("DATABASE_CREATE_API"), get_time_stamp())
        request_create_audio_api(create_api, audio_obj)
        sleep(0.5)

def main(ctx:Context=None):
    page_st = 1
    page_ed = 100000
    # 遍历[page_st, page_ed)页
    for now_page in range(page_st, page_ed):
        try:
            logger.info(f"\nscrape_areena_podcastit > 任务ID:{ctx.get('task_id')} page:{now_page} 准备入库, Context:{str(ctx)}")
            sleep(1)
            scrape_areena_podcastit_handler(ctx, scrape_mode=ctx.get("scrape_mode"), page=now_page)
            logger.success(f"\nscrape_areena_podcastit > 任务ID:{ctx.get('task_id')} page:{now_page} 入库完毕")
        except Exception as e:
            ctx.set("fail_count", ctx.get("fail_count") + 1)
            err_text = f"【scrape_areena_podcastit】 采集失败, 任务ID:{ctx.get('task_id')}, 页数:{now_page}, error:{e}"
            logger.error(err_text)
            # alarm(level="ERROR", text=err_text)
            if ctx.get("fail_count") > LIMIT_FAIL_COUNT:
                err_text = f"【scrape_areena_podcastit】 采集完毕, SERVER_NAME:{SERVER_NAME}, Context:{str(ctx)}"
                logger.error(err_text)
                alarm(level="ERROR", text=err_text)
                return
        finally:
            sleep(5)

if __name__ == "__main__":
    ctx = Context()
    ctx.set("task_id", str(uuid4()))
    ctx.set("fail_count", 0)

    # 关键字搜素入库
    # 遍历所有两位字母关键字
    # ctx.set("scrape_mode", "arrena_podcastit_search")
    # for query in ['aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai', 'aj', 'ak', 'al', 'am', 'an', 'ao', 'ap', 'aq', 'ar', 'as', 'at', 'au', 'av', 'aw', 'ax', 'ay', 'az']:
    # for query in ['ba', 'bb', 'bc', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bk', 'bl', 'bm', 'bn', 'bo', 'bp', 'bq', 'br', 'bs', 'bt', 'bu', 'bv', 'bw', 'bx', 'by', 'bz']:
    #     ctx.set("query", query)
    #     ctx.set("fail_count", 0)
    #     main(ctx)

    # 列表翻页入库
    ctx.set("scrape_mode", "arrena_podcastit_list")
    token_list = [
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTQ0L3BvcHVsYXI_ZXBpc29kZXNfYXNfc2VyaWVzPXRydWUiLCJhbmFseXRpY3MiOnsiY29udGV4dCI6eyJjb21zY29yZSI6eyJ5bGVfcmVmZXJlciI6InJhZGlvLnZpZXcuNTctNTJsdjlhVm4wLmt1bHR0dXVyaS5zdW9zaXR1aW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtMTQ0In19fX0.4DY_3kz1vsObXfBVRz14S1sKF_9m7moRK5-fXNtu9qs",
        # https://areena.yle.fi/podcastit/ohjelmat/30-3120?t=uusimmat
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMzEyMC9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0zMTIwLmhhdXNrYWFfc2V1cmFhLnV1c2ltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTMxMjAifX19fQ.OdRg3c2dD-ROHMDCErLc2gKPZA0Tt-rW8v-CYfQ2fI0",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMzEyMC9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0zMTIwLmhhdXNrYWFfc2V1cmFhLnN1b3NpdHVpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0zMTIwIn19fX0.1U4hjZKoe5dop0Ibws7UbYc1Vhl3V0XRhYKIvuzcH1Y",
        # https://areena.yle.fi/podcastit/ohjelmat/30-1605?t=uusimmat
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYwNS9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjA1LmtpaW5ub3N0YXZhdF9rZXNrdXN0ZWx1dC51dXNpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0xNjA1In19fX0.B91fRDUlM2CQtS8l0wQybNaFnXKs7MSFyM8Fh-J4g9I",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYwNS9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjA1LmtpaW5ub3N0YXZhdF9rZXNrdXN0ZWx1dC5zdW9zaXR1aW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtMTYwNSJ9fX19.s980j4ExdgYvSKqymyM5F7bUTHY_uHZ_ut4LRJ2Q7zI",
        # https://areena.yle.fi/podcastit/ohjelmat/30-3485
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMzQ4NS9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0zNDg1LnRydWVfY3JpbWUudXVzaW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtMzQ4NSJ9fX19.7SQmLEo_69g4ZLqA2EPirhKfzuXCZdlXLhT30Ak2y_A",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMzQ4NS9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0zNDg1LnRydWVfY3JpbWUuc3Vvc2l0dWltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTM0ODUifX19fQ.QIKLL7BjA5qV7_QJZRK4ChEwX38gfbBTlxfNyfNtC0g",
        # https://areena.yle.fi/podcastit/ohjelmat/30-1634
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYzNC9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjM0LnN5dmFsbGlzdGFfcG9oZGludGFhLnV1c2ltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTE2MzQifX19fQ.q5UP_7K0nNs5C8JWkb6Z13kZaNpWDtaC0E2adSFJxkQ",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYzNC9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjM0LnN5dmFsbGlzdGFfcG9oZGludGFhLnN1b3NpdHVpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0xNjM0In19fX0.o8jO4BJGQ-sVn7iHaUyISgIhhGoEU42db80Z4cJlahU",
        # https://areena.yle.fi/podcastit/ohjelmat/30-1635?t=uusimmat
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYzNS9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjM1LnBvbGl0aWlra2FfamFfdGFsb3VzLnV1c2ltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTE2MzUifX19fQ.ZpPjacxXoakpcvYU4IxbTd4InlFU78Nobr8o3XwmJfo",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTYzNS9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjM1LnBvbGl0aWlra2FfamFfdGFsb3VzLnN1b3NpdHVpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0xNjM1In19fX0.IelYb4Ipg9aPDmBht_F5CDkkfhnPehfd-2uCh7yGDqI",
        # https://areena.yle.fi/podcastit/ohjelmat/57-RypMmJdMD?t=uusimmat
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtNDI0NC9sYXRlc3Q_bWVkaWFfbGFuZ3VhZ2U9ZmluIiwiYW5hbHl0aWNzIjp7ImNvbnRleHQiOnsiY29tc2NvcmUiOnsieWxlX3JlZmVyZXIiOiJyYWRpby52aWV3LjU3LVJ5cE1tSmRNRC5rb21lZGlhX2phX3ZpaWhkZS51dXNpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC00MjQ0In19fX0.vp-cSbeO4yD1fmlJ6rfVV55AiAPkSzelH5INREqsXmE",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtNDI0NC9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSZtZWRpYV9sYW5ndWFnZT1maW4iLCJhbmFseXRpY3MiOnsiY29udGV4dCI6eyJjb21zY29yZSI6eyJ5bGVfcmVmZXJlciI6InJhZGlvLnZpZXcuNTctUnlwTW1KZE1ELmtvbWVkaWFfamFfdmlpaGRlLnN1b3NpdHVpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC00MjQ0In19fX0.Uk1HDirpy5fNE5p6RpCSY4uCx9g7RFzTOGbvwP-9A5o",
        # https://areena.yle.fi/podcastit/ohjelmat/30-165
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTY1L2V4dGVuZGVkLXJlY29tbWVuZGF0aW9ucyIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNjUubHVvbnRvX2phX3ltcGFyaXN0by5zdW9zaXRlbGx1dC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0xNjUifX19fQ.GKP5Li9Ksafj9GzQb2a0SV8k5Kiu2LVjq_T9xTx5p-s",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTY1L3BvcHVsYXI_ZXBpc29kZXNfYXNfc2VyaWVzPWZhbHNlIiwiYW5hbHl0aWNzIjp7ImNvbnRleHQiOnsiY29tc2NvcmUiOnsieWxlX3JlZmVyZXIiOiJyYWRpby52aWV3LjMwLTE2NS5sdW9udG9famFfeW1wYXJpc3RvLnN1b3NpdHVpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0xNjUifX19fQ.1l_OXYq2kh2EaBg3Ty1LVg47Z5jsLbc2RFD3okv7PHI",
        # https://areena.yle.fi/podcastit/ohjelmat/30-2582
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMjU4Mi9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0yNTgyLnRhcmlub2l0YV9waWVuaWxsZV9rb3J2aWxsZS51dXNpbW1hdC51bnRpdGxlZF9saXN0IiwieWxlX3BhY2thZ2VfaWQiOiIzMC0yNTgyIn19fX0.m8MlJ9T1Wc1_dm_aebWIbvvYsuYbTZh6UIvuNhOEBK0",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMjU4Mi9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0yNTgyLnRhcmlub2l0YV9waWVuaWxsZV9rb3J2aWxsZS5zdW9zaXR1aW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtMjU4MiJ9fX19.X9HrWqwGxFgAekJOq2HjjFfsqkUFu64y6etc3_LK8Wk",
        # https://areena.yle.fi/podcastit/ohjelmat/30-1582?t=uusimmat 👉 Terveys ja hyvinvointi
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTU4Mi9sYXRlc3Q_Z3JvdXBpbmc9b25kZW1hbmQucHVibGljYXRpb24uZGF0ZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNTgyLnRlcnZleXNfamFfaHl2aW52b2ludGkudXVzaW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtMTU4MiJ9fX19.05z5tOZcO4T-id_4Dk8tGmH_RzJ6f08dEQXvjyeX3dk",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTU4Mi9wb3B1bGFyP2VwaXNvZGVzX2FzX3Nlcmllcz1mYWxzZSIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy4zMC0xNTgyLnRlcnZleXNfamFfaHl2aW52b2ludGkuc3Vvc2l0dWltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTE1ODIifX19fQ.gXRxKRABCXEKbvrSuQf9sGoMP7B9BUdyJVkFehzlkIg",
        # ALL
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtNDkwL2xhdGVzdD9ncm91cGluZz1vbmRlbWFuZC5wdWJsaWNhdGlvbi5kYXRlIiwiYW5hbHl0aWNzIjp7ImNvbnRleHQiOnsiY29tc2NvcmUiOnsieWxlX3JlZmVyZXIiOiJyYWRpby52aWV3LjMwLTQ5MC5rYWlra2lfb2hqZWxtYXQudXVzaW1tYXQudW50aXRsZWRfbGlzdCIsInlsZV9wYWNrYWdlX2lkIjoiMzAtNDkwIn19fX0.F9_De_cJVPpDgoOVN1Wf_fU3M7A4Ea2Lb8GfAwWFBR0",
        "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtNDkwL3BvcHVsYXI_ZXBpc29kZXNfYXNfc2VyaWVzPWZhbHNlIiwiYW5hbHl0aWNzIjp7ImNvbnRleHQiOnsiY29tc2NvcmUiOnsieWxlX3JlZmVyZXIiOiJyYWRpby52aWV3LjMwLTQ5MC5rYWlra2lfb2hqZWxtYXQuc3Vvc2l0dWltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTQ5MCJ9fX19.r3BcoyUtOo8kOcqPX64N1B6PF51XDjNPDhihJ7EWoTs",
    ]
    for token in token_list:
        ctx.set("arrena_podcastit_list_token", token)
        main(ctx)