# 加载.env文件
from dotenv import load_dotenv
load_dotenv()

import json
from os import getenv, path, remove, makedirs
from time import time, sleep
from shutil import rmtree
from urllib.parse import urljoin
from traceback import format_exc
from utils.logger import logger
from utils.utime import random_sleep, get_now_time_string, format_second_to_time_string, get_time_stamp
from utils.file import get_file_size
from utils.lark import alarm_lark_text
from utils.ip import get_local_ip, get_public_ip
from database.crawler_audio_download_info import request_update_audio_api, request_get_audio_for_download_api
from handler.common import get_cloud_save_path_by_language

LOCAL_IP = get_local_ip()
''' 本地IP '''
SERVER_NAME = getenv("SERVER_NAME")
''' 服务名称 '''
LIMIT_FAIL_COUNT = int(getenv("LIMIT_FAIL_COUNT"))
''' 处理失败任务限制数 '''
LIMIT_LAST_COUNT = int(getenv("LIMIT_LAST_COUNT"))
''' 连续处理任务限制数 '''
CLOUD_TYPE = "obs" if getenv("OBS_ON", False) == "True" else "cos"
''' 云端存储类别，上传cos或者obs '''
if CLOUD_TYPE == "obs":
    # from utils.obs import upload_file as obs_upload_file
    from utils.obs import upload_file_v2 as obs_upload_file_v2
elif CLOUD_TYPE == "cos":
    from utils.cos import upload_file as cos_upload_file
else:
    raise ValueError("")
DOWNLOAD_PATH = getenv('DOWNLOAD_PATH')
''' 资源下载临时目录'''

def clean_path(save_path):
    ''' 清理下载目录 '''
    if path.exists(save_path):
        rmtree(save_path)
        print("clean_path > 已清理旧目录及文件: ", save_path)
    makedirs(save_path, exist_ok=True)
    print("clean_path > 已初始化目录: ", save_path)

def crawler_sleep(is_succ:bool, run_count:int, download_round:int):
    """
    随机等待

    :param is_succ: bool, 任务是否处理成功
    :param run_count: int, 任务处理次数
    :param download_round: int, 任务处理轮数
    """
    now_round = run_count//LIMIT_LAST_COUNT + 1
    if now_round > download_round:
        print(f"[INFO] > 触发轮数限制, 当前轮数：{now_round}")
        random_sleep(rand_st=30, rand_range=30)
        return
    if is_succ:
        random_sleep(rand_st=5, rand_range=5)
    else:
        random_sleep(rand_st=10, rand_range=10)

def download_handler(audio, save_path:str):
    from handler.areena_podcastit import areena_podcastit_download_handler
    download_path = areena_podcastit_download_handler(audio, save_path)
    if download_path == "":
        raise ValueError("areena_podcastit_download_handler get empty download file")
    return download_path

def main_pipeline(pid):
    sleep(15 * pid)
    logger.info(f"Pipeline > 进程 {pid} 开始执行")

    download_round = int(1)      # 当前下载轮数
    run_count = int(0)           # 持续处理的任务个数l
    continue_fail_count = int(0) # 连续失败的任务个数
    while True:
        audio = request_get_audio_for_download_api(
            url="%s?sign=%d"%(getenv("DATABASE_AUDIO_GET_API"), get_time_stamp()),
            query_source_type=int(getenv("DOWNLOAD_SOURCE_TYPE")),
            query_language=getenv("DOWNLOAD_LANGUAGE"),
        )
        if audio is None:
            logger.warning(f"Pipeline > 当前轮次: {download_round} | {run_count}, 进程 {pid} 无任务待处理, 等待中...")
            random_sleep(rand_st=20, rand_range=10)
            continue
        if audio.id <= 0 or audio.source_link == "":
            logger.warning(f"Pipeline > 当前轮次: {download_round} | {run_count}, 进程 {pid} 获取无效任务, 跳过处理...")
            random_sleep(rand_st=20, rand_range=10)
            continue
        try:
            run_count += 1
            audio_id = audio.id
            video_link = audio.source_link
            logger.info(f"Pipeline > 当前轮次: {download_round} | {run_count}, 进程 {pid} 处理任务 {audio_id} -- {video_link}")
            if audio.info not in [None, "", "{}"]:
                cloud_save_path = audio.info.get("cloud_save_path", "")
            else:
                cloud_save_path = ""

            # 下载
            time_1 = time()
            download_path = download_handler(audio, DOWNLOAD_PATH)
            spend_download_time = max(time() - time_1, 0.01) #下载花费时间
            logger.success(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 下载完成, from: {video_link}, to: {download_path}")
            
            # 上传云端
            time_2 = time()
            cloud_path = urljoin(
                get_cloud_save_path_by_language(
                    save_path=cloud_save_path if cloud_save_path !='' else getenv("CLOUD_SAVE_PATH"),
                    lang_key=audio.language
                ), 
                path.basename(download_path)
            )
            logger.info(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 准备上传 `{CLOUD_TYPE}`, from: {download_path}, to: {cloud_path}")
            if CLOUD_TYPE == "obs":
                cloud_link = obs_upload_file_v2(
                    from_path=download_path, to_path=cloud_path
                )
            elif CLOUD_TYPE == "cos":
                cloud_link = cos_upload_file(
                    from_path=download_path, to_path=cloud_path
                )
            else:
                raise ValueError("invalid cloud type")
            spend_upload_time = max(time() - time_2, 0.01) #上传花费时间
            logger.success(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 上传完成, from: {download_path}, to: {cloud_link}")
            
            # 更新数据库
            audio.status = 2 # 2:已上传云端
            audio.cloud_type = 2 if CLOUD_TYPE == "obs" else 1 # 1:cos 2:obs
            audio.cloud_path = cloud_link
            audio.update_db(force_update=True)
            logger.success(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 更新数据库完成")
            
            # 日志记录
            spend_total_time = int(time() - time_1) #总花费时间
            file_size = get_file_size(download_path)
            logger.info(
                f"Pipeline > 进程 {pid} 完成处理任务 {audio_id}, 已上传至 {cloud_path}, 文件大小: {file_size} MB, 共处理了 {format_second_to_time_string(spend_total_time)}"
            )
            
            # 移除本地文件
            remove(download_path)
            logger.success(f"Pipeline > 进程 {pid} 移除本地文件 {download_path}")

            # 通知
            notice_text = f"[Podcastit Crawler] download pipeline success. \
                \n\t下载服务: {SERVER_NAME} | 进程: {pid} \
                \n\t下载信息: 轮数 {download_round} | 处理总数 {run_count} | 连续失败数 {continue_fail_count} \
                \n\t资源信息: {audio.id} | {audio.vid} | {audio.language} \
                \n\tLink: {audio.source_link} -> {audio.cloud_path} \
                \n\t资源共 {file_size:.2f}MB , 共处理了{format_second_to_time_string(spend_total_time)} \
                \n\t下载时长: {format_second_to_time_string(spend_download_time)} , 上传时长: {format_second_to_time_string(spend_upload_time)} \
                \n\t下载均速: {file_size/spend_download_time:.2f}M/s , 上传均速: {file_size/spend_upload_time:.2f}M/s \
                \n\tIP: {LOCAL_IP} | {get_public_ip()}"
            logger.info(notice_text)
            alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_INFO"), text=notice_text)

            logger.success(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 完毕")
        except KeyboardInterrupt:
            logger.warning(f"Pipeline > 进程 {pid} interrupted processing {audio_id}, reverting...")
            # 任务回调
            audio.status = 0
            audio.lock = 0
            audio.update_db()
            raise KeyboardInterrupt
        # except BrokenPipeError as e: # 账号被封处理
        #     return
        except Exception as e:
            continue_fail_count += 1
            time_fail = time()
            logger.error(f"Pipeline > 进程 {pid} 处理任务 {audio_id} 失败, 错误信息:{e}")
            # 任务回调
            audio.status = -1
            audio.lock = 0
            audio.comment += f'<div class="download_pipeline">pipeline error:{e}, error_time:{get_now_time_string()}</div>'
            audio.update_db(force_update=True)
            # 告警
            notice_text = f"[Podcastit Crawler | ERROR] download pipeline failed. \
                \n\t下载服务: {SERVER_NAME} | {pid} \
                \n\t下载信息: 轮数 {download_round} | 处理总数 {run_count} | 连续失败数 {continue_fail_count}\
                \n\t资源信息: {audio.id} | {audio.vid} | {audio.language} \
                \n\tSource Link: {audio.source_link} \
                \n\t共处理了{format_second_to_time_string(int(time_fail-time_1))} \
                \n\tIP: {LOCAL_IP} | {get_public_ip()} \
                \n\tError: {e} \
                \n\t告警时间: {get_now_time_string()} \
                \n\tStack Info: {format_exc()[-500:]}"
            logger.error(notice_text)
            alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_INFO"), text=notice_text)
            # 失败过多直接退出
            if continue_fail_count > LIMIT_FAIL_COUNT:
                logger.error(f"Pipeline > 进程 {pid} 失败过多超过{continue_fail_count}次, 异常退出")
                alarm_lark_text(webhook=getenv("NOTICE_WEBHOOK_ERROR"), text=notice_text)
                # 退出登陆
                # if getenv("CRAWLER_SWITCH_ACCOUNT_ON", False) == "True":
                #     ac.logout(is_invalid=True, comment=f"{SERVER_NAME}失败过多退出, {e}")
                return
            crawler_sleep(is_succ=False, run_count=run_count, download_round=download_round)
            continue
        else:
            continue_fail_count = 0
            crawler_sleep(is_succ=True, run_count=run_count, download_round=download_round)
        finally:
            download_round = run_count//LIMIT_LAST_COUNT + 1


if __name__ == "__main__":
    # 清理旧目录文件
    clean_path(DOWNLOAD_PATH)

    # 单进程
    # main_pipeline(0)

    # 多进程
    import multiprocessing
    # PROCESS_NUM = 1 #同时处理的进程数量
    PROCESS_NUM = int(getenv("PROCESS_NUM"))
    try:
        with multiprocessing.Pool(PROCESS_NUM) as pool:
            for i in range(PROCESS_NUM):
                pool.apply_async(main_pipeline, (i,))
            pool.close()
            pool.join()
    except Exception as e:
        logger.critical(f"[PANIC] > Exception raise: {e.__class__} | {e}")
        pool.terminate()