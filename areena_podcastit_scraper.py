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
from database.crawler_audio_download_info import request_create_audio_api
from handler.areena_podcastit import request_podcastit_list, parse_podcastit_list
from model.areena_podcastit import format_areena_audio_object

SERVER_NAME = getenv("SERVER_NAME")
''' 服务名称 '''
LIMIT_FAIL_COUNT = int(getenv("LIMIT_FAIL_COUNT"))
''' 处理失败任务限制数 '''

def test():
    # 请求播客列表接口
    # response = request_podcastit_list(url="https://areena.api.yle.fi/v1/ui/content/list", page=1, page_size=16)
    # parse_podcastit_list(response)

    # 解析播客id
    # print(get_areena_aid("yleareena://items/1-50647813"))
    # print(get_areena_aid("https://areena.yle.fi/podcastit/1-72758069"))

    # 格式化音频
    # audio_obj = format_audio_object(task_id="test_task", audio_url="https://areena.yle.fi/podcastit/1-72758069", duration=230, language="fi", source_id="")

    # 测试入库
    # url = "%s?sign=%d" % (getenv("DATABASE_CREATE_API"), get_time_stamp())
    # create_api = "%s?sign=%d" % ("https://magicmir.52ttyuyin.com/crawler_api/create_audio_record", get_time_stamp())
    # request_create_audio_api(create_api, audio_obj)
    pass
    
def scrape_areena_podcastit_handler(task_id:str, page:int, page_size:int=16):
    # 请求播客列表接口
    response = request_podcastit_list(
        url="https://areena.api.yle.fi/v1/ui/content/list",
        page=page,
        page_size=page_size,
    )
    for audio_url in parse_podcastit_list(response):
        logger.debug(f"parse_podcastit_list > audio_url:{audio_url}")
        # 解析播客id
        # print(get_areena_aid("yleareena://items/1-50647813"))
        # print(get_areena_aid("https://areena.yle.fi/podcastit/1-72758069"))

        # 格式化音频
        audio_obj = format_areena_audio_object(
            task_id=task_id,
            audio_url=audio_url,
            duration=0,
            language="fi",
            source_id="",
        )

        # 入库
        create_api = "%s?sign=%d" % (getenv("DATABASE_CREATE_API"), get_time_stamp())
        request_create_audio_api(create_api, audio_obj)
        sleep(0.5)
        

def main():
    continue_fail_count = 0

    # 任务id
    task_id = str(uuid4())
    page_st = 6
    page_ed = 100000
    page_size = 16
    # 遍历[page_st, page_ed)页
    for page in range(page_st, page_ed):
        try:
            scrape_areena_podcastit_handler(task_id, page, page_size)
            logger.success(f"scrape_areena_podcastit > page:{page} page_size:{page_size} 入库完毕")
        except Exception as e:
            err_text = f"【scrape_areena_podcastit】 采集失败, task_id:{task_id}, page:{page}, page_size:{page_size}, error:{e}"
            logger.error(err_text)
            continue_fail_count += 1
            alarm(level="ERROR", text=err_text)
            if continue_fail_count > LIMIT_FAIL_COUNT:
                err_text = f"【scrape_areena_podcastit】 失败过多退出采集, server_name:{SERVER_NAME}, task_id:{task_id}"
                logger.error(err_text)
                alarm(level="ERROR", text=err_text)
                exit(1)
        finally:
            sleep(20)

if __name__ == "__main__":
    main()
    # test()