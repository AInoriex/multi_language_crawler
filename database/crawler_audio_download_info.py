import json
import time
import random
import requests
from os import getenv
from utils.logger import logger
from utils.utime import get_time_stamp

TABLE_NAME = str("crawler_download_info")

class Audio:
    """
    音频数据

    Attributes:
        id: 主键id
        vid: 音频ID
        position: 1: cas, 2: cuhk, 3: quwan
        source_type: 1: Bilibili, 2: 喜马拉雅, 3: YouTube
        source_link: 完整音频链接
        duration: 原始长度
        language: 音频主要语言
        cloud_type: 云存储类型
        cloud_path: 云存储的路径
        result_path: 处理结果路径
        status: 0: 已爬取, 1: 本地已下载, 2: 已上传云端未处理, 3: 已处理未上传, 4: 已处理已上传, -1 失败
        lock: 处理锁, 0: 未锁定, 1: 锁定
        info: meta数据, json格式
        comment: 备注
    """

    def __init__(
        self,
        vid: str = None,
        source_type: int = 3,
        cloud_path: str = "",
        id: int = 0,
        position: int = 1,
        cloud_type: int = 0,
        source_link: str = "",
        duration: int = 0,
        language: str = "",
        status=0,
        lock=0,
        info={},
        source_id: str = "",
        comment: str = "",
    ):
        self.id = id
        self.vid = vid
        self.position = position
        self.source_type = source_type
        self.source_link = source_link
        self.duration = duration
        self.cloud_type = cloud_type
        self.cloud_path = cloud_path
        self.language = language
        self.status = status
        self.lock = lock
        self.info = info
        self.source_id = source_id
        self.comment = comment

    def __str__(self) -> str:
        return (
            f"Audio(vid={self.vid}, position={self.position}, source_id={self.source_id}, "
            f"source_type={self.source_type}, source_link={self.source_link}, duration={self.duration}, "
            f"cloud_type={self.cloud_type}, cloud_path={self.cloud_path},"
            f"language={self.language}, status={self.status}, `lock`={self.lock}, info={self.info})"
        )
    
    def dict(self)->dict:
        return {
            "id": self.id,
            "vid": self.vid,
            "position": self.position,
            "source_type": self.source_type,
            "source_link": self.source_link,
            "duration": self.duration,
            "cloud_type": self.cloud_type,
            "cloud_path": self.cloud_path,
            "language": self.language,
            "status": self.status,
            "lock": self.lock,
            "info": self.info,
            "source_id": self.source_id,
            "comment": self.comment,
        }

    # 更新info字段
    def update_info(self, add_info:dict):
        # if self.info in [None, "", "{}"]:
        #     self.info = add_info
        # else:
        #     self_info = json.loads(self.info)
        #     self.info = self_info | add_info # Python3.9+
        self.info = self.info | add_info # Python3.9+

    # 更新数据库
    def update_db(self, db_url:str=getenv("DATABASE_AUDIO_UPDATE_API")):
        """
        update a audio record in database with api

        :param db_url: str, request api, default is `DATABASE_VIDEO_UPDATE_API`
        :return: None
        """
        params = {
            "sign": get_time_stamp()
        }
        reqbody = {
            "id": self.id,
            # "vid": self.vid,
            "status": self.status,
            "cloud_type": self.cloud_type,
            "cloud_path": self.cloud_path,
            "info": json.loads(self.info),
            "comment": self.comment,
            "duration": self.duration,
        }
        logger.debug(f"update_db > update request | url:{db_url} params:{params} body:{reqbody}")
        resp = requests.post(url=db_url, params=params, json=reqbody)
        assert resp.status_code == 200
        resp_json = resp.json()
        logger.debug("update_db > update response | status_code:%d, content:%s"%(resp_json["code"], resp_json["msg"]))
        if resp_json["code"] != 0:
            raise Exception(f"update_db failed, req:{reqbody}, resp:{resp.status_code}|{str(resp.content, encoding='utf-8')}")
        logger.info(f"update_db > update succeed, req:{reqbody}")

def request_create_audio_api(url:str, audio:Audio, retry:int=3):
    ''' 调用crawler_audio_download_info数据库接口创建音频记录 '''
    try:
        params = {
            "sign": get_time_stamp()
        }
        req = audio.dict()
        resp = requests.post(url=url, params=params, json=req, timeout=5, verify=True)
        assert resp.status_code == 200
        resp_json = resp.json()
        logger.debug("request_create_audio_api > resp detail, status_code:%d, content:%s"%(resp_json["code"], resp_json["msg"]))
        resp_code = resp_json.get("code")
        if resp_code == 0:
            logger.info(f"request_create_audio_api > 创建数据成功 vid:{req.get('vid')}, link:{req.get('source_link')}")
        elif resp_code == 25000:
            logger.info(f"request_create_audio_api > 资源存在, 跳过创建 status_code:{resp_json.get('code')}, content:{resp_json.get('msg')}")
        else:
            raise Exception(f"资源创建失败, req:{req}, resp:{str(resp.content, encoding='utf-8')}")
    except Exception as e:
        logger.error(f"request_create_audio_api > {url}入库处理失败: {e}")
        if retry > 0:
            logger.info(f"request_create_audio_api > 重新尝试入库, 剩余尝试次数: {retry}")
            time.sleep(1)
            return request_create_audio_api(url, audio, retry-1)
        else:
            logger.error(f"request_create_audio_api > {url}入库失败, 达到最大重试次数")
            raise e

def request_get_audio_for_download_api(
        url:str=getenv("DATABASE_AUDIO_GET_FOR_DOWNLOAD_API"),
        query_id:int=0,
        query_source_type:int=int(getenv("DOWNLOAD_SOURCE_TYPE")),
        query_language:str=getenv("DOWNLOAD_LANGUAGE"),
    )->Audio|None:
    """
    get a audio for downloading from api

    :param url: str, request api, default is `DATABASE_AUDIO_GET_FOR_DOWNLOAD_API`
    :param query_id: int, audio id in database, default is 0 which means get a random audio
    :param query_source_type: int, source type of audio, default is `DOWNLOAD_SOURCE_TYPE` in .env
    :param query_language: str, language of audio, default is `DOWNLOAD_LANGUAGE` in .env
    :return: Audio or None
    """
    try:
        params = {
            "sign": get_time_stamp(),
            "id": query_id,
            "source_type": query_source_type,
            "language": query_language,
            "limit": 1
        }
        # logger.debug(f"request_get_audio_for_download_api > Get list Request | url:{url} params:{params}")
        resp = requests.get(url=url, params=params)
        # logger.debug(f"request_get_audio_for_download_api > Get list Response | status_code:{resp.status_code}, content:{str(resp.content, encoding='utf-8')}")
        assert resp.status_code == 200
        resp_json = resp.json()
        logger.debug(f"request_get_audio_for_download_api > Get list Response detail | status_code:{resp_json['code']}, content:{resp_json['msg']}")
        if len(resp_json["data"]["result"]) <= 0:
            logger.warning("request_get_audio_for_download_api > No audio to download")
            return None
        resp_data:dict = resp_json["data"]["result"][0]
        info_dict = json.loads(resp_data.get("info", "{}"))
        audio = Audio(
            id=resp_data.get("id", 0),
            vid=resp_data.get("vid", ""),
            position=resp_data.get("position", 0),
            source_type=resp_data.get("source_type", 0),
            source_link=resp_data.get("source_link", ""),
            duration=resp_data.get("duration", 0),
            cloud_type=resp_data.get("cloud_type", 0),
            cloud_path=resp_data.get("cloud_path", ""),
            language=resp_data.get("language", ""),
            status=resp_data.get("status", 0),
            lock=resp_data.get("lock", 0),
            info=info_dict,
            comment=resp_data.get("comment", "")
        )
        return audio
    except Exception as e:
        logger.error(f"request_get_audio_for_download_api > get audio failed, url:{url}, req:{params}, error: {e}")
        return None

def request_update_audio_api(url:str, audio:Audio):
    """
    update a audio record in database with api

    :param url: str, request api
    :param audio: Audio, the audio record to be updated
    :return: None
    """
    params = {
        "sign": get_time_stamp()
    }
    reqbody = {
        "id": audio.id,
        # "vid": audio.vid,
        "status": audio.status,
        "cloud_type": audio.cloud_type,
        "cloud_path": audio.cloud_path,
        "info": audio.info,
        "comment": audio.comment,
        "duration": audio.duration,
    }
    # logger.debug(f"request_update_audio_api > update request | url:{url} params:{params} body:{reqbody}")
    resp = requests.post(url=url, params=params, json=reqbody)
    assert resp.status_code == 200
    resp_json = resp.json()
    # logger.debug("request_update_audio_api > update response | status_code:%d, content:%s"%(resp_json["code"], resp_json["msg"]))
    if resp_json["code"] != 0:
        raise Exception(f"request_update_audio_api failed, req:{reqbody}, resp:{resp.status_code}|{str(resp.content, encoding='utf-8')}")
    else:
        logger.info(f"request_update_audio_api > update succeed, req:{reqbody}")


if __name__ == "__main__":
    # Example Usage
    audio_obj = Audio(
        vid="VID12345",
        position=1,
        source_type=1,
        source_link="https://www.youtube.com/watch?v=12345",
        duration=100,
        cloud_type=2,
        cloud_path="/cloud/path/to/audio",
        language="en",
        status=0,
        lock=0,
        info='{"key": "value"}',
        source_id="UCgdiE5jT-77eUMLXn66NLCQ"
    )
    print(audio_obj)
    pass
