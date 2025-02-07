import json
from utils.logger import logger
from database.crawler_download_info import Video
from database.crawler_audio_download_info import Audio

def get_video_id(url:str):
    ''' 使用正则表达式匹配 URL 中的特定部分
    exp. https://www.svtplay.se/video/j16gBxm/vanmakt -> j16gBxm
    '''
    import re
    pattern = r'https://www\.svtplay\.se/video/([^/]+)/'
    match = re.search(pattern, url)
    if not match:
        raise Exception(f"extract svtplay video id failed, url：{url}")
    return match.group(1)  # 返回匹配到的第一个捕获组的内容

def format_svtplay_video_object(task_id:str, video_url:str, duration:int=0, language:str="sv", source_id:str="")->Video:
    ''' 格式化信息为数据库入库对象
    :param video_url: 视频URL eg: https://www.youtube.com/watch?v=XYjL_pXK8V8
    :param duration: 时长
    :param language: 语言
    :param task_id: 任务id
    :param source_id: 来源id
    :return: Video
    '''
    vid = f"svt_{get_video_id(video_url)}"
    info_dict ={}
    info_dict['cloud_save_path'] = "/QUWAN_DATA/language/Ruidianyu/svtplay/"
    info_dict['task_id'] = task_id
    info = json.dumps(info_dict)

    # TODO 改造yaml读取
    video_obj = Video(
        id=int(0),
        vid=vid,
        position=int(3),
        source_type=int(14),
        source_link=str(video_url),
        language=str(language),
        duration=int(duration),
        info=info,
        source_id=source_id
    )
    logger.debug(f"format_svtplay_video_object > {video_obj}")
    return video_obj

def format_svtplay_audio_object(task_id:str, video_url:str, duration:int=0, language:str="sv", source_id:str="")->Audio:
    ''' 格式化信息为数据库入库对象
    :param video_url: 视频URL eg: https://www.youtube.com/watch?v=XYjL_pXK8V8
    :param duration: 时长
    :param language: 语言
    :param task_id: 任务id
    :param source_id: 来源id
    :return: Audio
    '''
    vid = f"svt_{get_video_id(video_url)}"
    info_dict ={}
    info_dict['cloud_save_path'] = "/QUWAN_DATA/language/Ruidianyu/svtplay/"
    info_dict['task_id'] = task_id
    info = json.dumps(info_dict)

    # TODO 改造yaml读取
    audio_obj = Audio(
        id=int(0),
        vid=vid,
        position=int(3),
        source_type=int(14),
        source_link=str(video_url),
        language=str(language),
        duration=int(duration),
        info=info,
        source_id=source_id
    )
    logger.debug(f"format_svtplay_audio_object > {audio_obj}")
    return audio_obj