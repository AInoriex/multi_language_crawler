from os import getenv
from pprint import pprint
from time import sleep
from uuid import uuid4
from database.crawler_download_info import Video
from handler.svtplay import request_video_info_api, svtplay_video_download_handler, svtplay_video_meta_handler, request_svtplay_kategori_page, parse_svtplay_kategori_page, extract_video_id, format_svtplay_video_object
from utils.lark import alarm
from utils.context import Context
from utils.logger import logger
from utils.utime import compare_time1_to_time2

SERVER_NAME = getenv("SERVER_NAME")
''' 服务名称 '''
LIMIT_FAIL_COUNT = int(getenv("LIMIT_FAIL_COUNT"))
''' 处理失败任务限制数 '''

def scrape_svtplay_video_handler(ctx:Context, url:str):
    # html = "downloads/scen.txt"
    # with open(html, mode="r", encoding="utf-8") as f:
    #     html = f.read()

    resp = request_svtplay_kategori_page(url)
        # "https://www.svtplay.se/video/KrJXG2Y/marten-cvetkovic-en-standup-med-marten-andersson"
    # )
    html = resp.text

    hrefs = parse_svtplay_kategori_page(html)
    print(f"一共{len(hrefs)}条数据")
    pprint(hrefs)
    sleep(3)

    # 入库
    for href in hrefs:
        try:
            source_link = "https://www.svtplay.se" + href
            # print(source_link)
            ctx.set("source_link", source_link)
            video_obj = format_svtplay_video_object(
                task_id=ctx.get("task_id"),
                video_url=source_link,
            )
            video_obj.insert_db()
        except Exception as e:
            ctx.set("fail_count", ctx.get("fail_count") + 1)
            err_text = f"[scrape_svtplay_video] 采集失败, 任务ID:{ctx.get('task_id')}, error:{e}"
            logger.error(err_text)
            alarm(level="ERROR", text=err_text)
            if ctx.get("fail_count") > LIMIT_FAIL_COUNT:
                err_text = f"[scrape_svtplay_video] 采集失败过多, SERVER_NAME:{SERVER_NAME}, Context:{str(ctx)}"
                logger.error(err_text)
                alarm(level="ERROR", text=err_text)
                return
            sleep(0.5)

def main(ctx:Context=None):
    url_list = [
        # "https://www.svtplay.se/video/KrJXG2Y/marten-cvetkovic-en-standup-med-marten-andersson"
        "https://www.svtplay.se/kategori/serier?tab=all",
        "https://www.svtplay.se/kategori/nyheter?tab=all",
        "https://www.svtplay.se/kategori/dokumentar?tab=all",
        "https://www.svtplay.se/kategori/sport?tab=all",
        "https://www.svtplay.se/kategori/barn?tab=all",
        "https://www.svtplay.se/kategori/filmer?tab=all",
        "https://www.svtplay.se/kategori/underhallning?tab=all",
        "https://www.svtplay.se/kategori/melodifestivalen?tab=all",
        "https://www.svtplay.se/kategori/livsstil-och-reality?tab=all",
        "https://www.svtplay.se/kategori/musik?tab=all",
        "https://www.svtplay.se/kategori/fakta?tab=all",
        "https://www.svtplay.se/kategori/humor?tab=all",
        "https://www.svtplay.se/kategori/kultur?tab=all",
        "https://www.svtplay.se/kategori/samhalle?tab=all",
        "https://www.svtplay.se/kategori/djur-och-natur?tab=all",
        "https://www.svtplay.se/kategori/scen?tab=all",
        "https://www.svtplay.se/kategori/oppet-arkiv?tab=all",
    ]
    for url in url_list:
        scrape_svtplay_video_handler(ctx, url)
        info_text = f"[scrape_svtplay_video] {url} 采集完成, 任务ID:{ctx.get('task_id')}"
        alarm(level="debug", text=info_text)
 
if __name__ == "__main__":
    ctx = Context()
    ctx.set("task_id", str(uuid4()))
    ctx.set("fail_count", 0)
    main(ctx)