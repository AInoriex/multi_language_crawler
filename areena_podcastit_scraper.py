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
from handler.areena_podcastit import request_podcastit_list_api, request_podcastit_search_api, parse_podcastit_list
from model.areena_podcastit import format_areena_audio_object

SERVER_NAME = getenv("SERVER_NAME")
''' 服务名称 '''
LIMIT_FAIL_COUNT = int(getenv("LIMIT_FAIL_COUNT"))
''' 处理失败任务限制数 '''
    
def scrape_areena_podcastit_handler(ctx:Context, scrape_mode:str="", page:int=1, _page_size:int=16):
    if not scrape_mode or scrape_mode not in ["list", "search"]:
        raise ValueError("请指定scrape_areena_podcastit_handler scrape_mode采集模式（list/search）")
    if scrape_mode == "list":
        # 请求播客列表接口
        response = request_podcastit_list_api(
            url="https://areena.api.yle.fi/v1/ui/content/list",
            page=page,
            page_size=_page_size,
        )
    elif scrape_mode == "search":
        # 请求播客搜索接口
        if ctx.get("query") is None:
            raise ValueError("请指定scrape_areena_podcastit_handler搜索关键词")
        response = request_podcastit_search_api(
            url="https://areena.api.yle.fi/v1/ui/search",
            query=ctx.get("query"),
            page=page,
            page_size=_page_size,
        )
    for audio_url in parse_podcastit_list(response):
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

            # scrape_areena_podcastit_handler(task_id=task_id, mode="list", page=page)
            scrape_areena_podcastit_handler(ctx, scrape_mode="search", page=now_page)

            logger.success(f"\nscrape_areena_podcastit > 任务ID:{ctx.get('task_id')} page:{now_page} 入库完毕")
        except Exception as e:
            err_text = f"【scrape_areena_podcastit】 采集失败, 任务ID:{ctx.get('task_id')}, 页数:{now_page}, error:{e}"
            logger.error(err_text)
            ctx.set("fail_count", ctx.get("fail_count") + 1)
            alarm(level="ERROR", text=err_text)
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
    # 遍历所有两位字母关键字
    # for query in ['aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ag', 'ah', 'ai', 'aj', 'ak', 'al', 'am', 'an', 'ao', 'ap', 'aq', 'ar', 'as', 'at', 'au', 'av', 'aw', 'ax', 'ay', 'az']:
    for query in ['ba', 'bb', 'bc', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bk', 'bl', 'bm', 'bn', 'bo', 'bp', 'bq', 'br', 'bs', 'bt', 'bu', 'bv', 'bw', 'bx', 'by', 'bz']:
        ctx.set("query", query)
        ctx.set("fail_count", 0)
        main(ctx)