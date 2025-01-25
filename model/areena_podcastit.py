import json
from utils.logger import logger
from database.crawler_audio_download_info import Audio

def get_areena_aid(url:str):
    """
    Extract areena id from given url.

    Parameters:
    url (str): url of areena media

    Returns:
    str: areena id, start with "areena_{id}"

    Raises:
    ValueError: given url is not supported url which may not from areena
    """
    # https://areena.yle.fi/podcastit/1-72758068
    if url.startswith("https://areena.yle.fi/podcastit/"):
        return "areena_" + url.split("https://areena.yle.fi/podcastit/")[1]
    # yleareena://items/1-72758068
    elif url.startswith("yleareena://items/"):
        return "areena_" + url.split("yleareena://items/")[1]
    else:
        # return ""
        raise ValueError(f"get_areena_aid by {url} failed")

def format_areena_audio_object(task_id:str, audio_url:str, duration:int=0, language:str="", source_id:str="")->Audio:
    ''' 格式化信息为数据库入库对象
    :param audio_url: 音频URL eg: https://www.youtube.com/watch?v=XYjL_pXK8V8
    :param duration: 时长
    :param language: 语言
    :param task_id: 任务id
    :param source_id: 来源id
    :return: Audio
    '''
    # 提取信息
    aid = get_areena_aid(audio_url)

    # 封装info
    info_dict ={}
    info_dict['cloud_save_path'] = "/QUWAN_DATA/language/Fenlanyu/areena/"
    info_dict['task_id'] = task_id
    info = json.dumps(info_dict)

    # TODO 改造yaml读取
    audio_obj = Audio(
        id=int(0),
        vid=aid,
        position=int(3),
        source_type=int(13),
        source_link=str(audio_url),
        language=str(language),
        duration=int(duration),
        info=info,
        source_id=source_id
    )
    logger.debug(f"format_areena_audio_object > {audio_obj}")
    return audio_obj
