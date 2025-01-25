import time
import random
from os import getenv
from typing import List

TABLE_NAME = str("crawler_download_info")

class Video:
    """
    视频数据

    Attributes:
        id: 主键id
        vid: 视频ID
        position: 1: cas, 2: cuhk, 3: quwan
        source_type: 1: Bilibili, 2: 喜马拉雅, 3: YouTube
        source_link: 完整视频链接
        duration: 原始长度
        language: 视频主要语言
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
            f"Video(vid={self.vid}, position={self.position}, source_id={self.source_id}, "
            f"source_type={self.source_type}, source_link={self.source_link}, duration={self.duration}, "
            f"cloud_type={self.cloud_type}, cloud_path={self.cloud_path}, "
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
            "source_id": self.source_id
        }

if __name__ == "__main__":
    # Example Usage
    video_obj = Video(
        vid="VID12345",
        position=1,
        source_type=1,
        source_link="https://www.youtube.com/watch?v=12345",
        duration=100,
        cloud_type=2,
        cloud_path="/cloud/path/to/video",
        language="en",
        status=0,
        lock=0,
        info='{"key": "value"}',
        source_id="UCgdiE5jT-77eUMLXn66NLCQ"
    )
    print(video_obj)
    pass
