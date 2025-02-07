from os import getenv, path 
import requests
from database.crawler_download_info import Video
from database.crawler_audio_download_info import Audio
from handler.yt_dlp import download_video, download_audio
from model.svtplay import get_video_id
from utils.logger import logger

_PROXIES = {'http': getenv("HTTP_PROXY"),'https': getenv("HTTP_PROXY")} if getenv("HTTP_PROXY", "") != "" else None

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

def request_video_info_api(url:str):
    # https://www.svtplay.se/video/jNgQ3XK/varldens-starkaste-bella
    # https://www.svtplay.se/video/8opYX4N/dokument-utifran-inuti-krigets-ryssland
    try:
        vid = get_video_id(url)
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "origin": "https://www.svtplay.se",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.svtplay.se/",
            "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Microsoft Edge\";v=\"132\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
        }
        url = f"https://video.svt.se/video/{vid}"
        response = requests.get(url, headers=headers, cookies=None, proxies=_PROXIES)

        print(f"request_video_info_api > response.status_code: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"request_video_info_api failed, status_code: {response.status_code}")
        # print(f"request_video_info_api > response.text: {response.text}")
        # dump_info(response.text, r"doc\request_video_info_api-response_example.json")
        return response
        
        # 获取视频url
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"}
        # base_url = "https://www.svtplay.se"

        # response = requests.get(url, headers=headers)
        # if response.status_code != 200:
        #     raise Exception(f"{url}请求失败，状态码：{response.status_code}")
        # 解析mp4链接
        # sub_video_url = tree.xpath('//*[@id="play_main-content"]/div/div[1]/div[2]/div/div/div/a[1]/@href')
        # video_url = f"{base_url}{sub_video_url[0]}"
        # print(f"视频链接：{video_url}")
        # 下载
        # download_video_yt_dlp(video_url)

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

def parse_video_info_response(response:requests.Response):
    # 解析响应，提取视频信息
    data_json = response.json()

    # is_video_valid(response)
    media_info = {}
    media_info["svtId"] = data_json["svtId"] if data_json.get("svtId") else ""
    media_info["contentDuration"] = data_json["contentDuration"] if data_json.get("contentDuration") else 0
    media_info["blockedForChildren"] = data_json["blockedForChildren"] if data_json.get("blockedForChildren") else False
    media_info["programTitle"] = data_json["programTitle"] if data_json.get("programTitle") else ""
    media_info["episodeTitle"] = data_json["episodeTitle"] if data_json.get("episodeTitle") else ""
    media_info["rights"] = data_json["rights"] if data_json.get("rights") else {}
    media_info["thumbnailMap"] = data_json["thumbnailMap"] if data_json.get("thumbnailMap") else {}
    return media_info

def is_video_valid(response:requests.Response):
    # 判断视频播放权限
    from utils.utime import compare_time1_to_time2
    data_json = response.json()

    rights = data_json["rights"]
    if rights.get("geoBlockedSweden", False):
        raise Exception("视频仅能在瑞典播放")
    
    valid_from = rights.get("validFrom")
    if valid_from and compare_time1_to_time2(valid_from, "now"):
        raise Exception(f"视频未开始播放, validFrom:{valid_from}")
    
    valid_to = rights.get("validTo", "")
    if valid_to and compare_time1_to_time2("now", valid_to):
        raise Exception(f"视频已过期, validTo:{valid_to}")

    return

def svtplay_video_download_handler(video:Video, save_path:str=""):
    # 下载视频文件
    if video.source_link == "":
        raise ValueError("video.source_link is empty")
    filename = path.join(save_path, f"{video.vid}.mp4")
    download_path = download_video(video.source_link, filename)
    logger.debug(f"svtplay_video_download_handler > {video.vid}下载{video.source_link}成功, download_path:{download_path}")
    return download_path

def svtplay_audio_download_handler(audio:Audio, save_path:str=""):
    # 下载音频文件
    if audio.source_link == "":
        raise ValueError("audio.source_link is empty")
    filename = path.join(save_path, f"{audio.vid}.m4a")
    download_path = download_audio(audio.source_link, filename)
    logger.debug(f"svtplay_audio_download_handler > {audio.vid}下载{audio.source_link}成功, download_path:{download_path}")
    return download_path

def svtplay_video_meta_handler(video:Video):
    # 更新媒体信息
    if video.source_link == "":
        raise ValueError("video.source_link is empty")
    resp = request_video_info_api(video.source_link)
    logger.debug(f"svtplay_video_meta_handler > {video.vid}请求{video.source_link}成功")
    meta = parse_video_info_response(resp)
    logger.debug(f"svtplay_video_meta_handler > {video.vid}解析{video.source_link}成功")
    video.duration = meta["contentDuration"]
    video.update_info(meta)
    video.update_db()
    logger.debug(f"svtplay_video_meta_handler > {video.vid}更新媒体信息成功")

def svtplay_audio_meta_handler(audio:Audio):
    # 更新媒体信息
    if audio.source_link == "":
        raise ValueError("audio.source_link is empty")
    resp = request_video_info_api(audio.source_link)
    logger.debug(f"svtplay_audio_meta_handler > {audio.vid}请求{audio.source_link}成功")
    meta = parse_video_info_response(resp)
    logger.debug(f"svtplay_audio_meta_handler > {audio.vid}解析{audio.source_link}成功")
    audio.duration = meta["contentDuration"]
    audio.update_info(meta)
    audio.update_db()
    logger.debug(f"svtplay_audio_meta_handler > {audio.vid}更新媒体信息成功")

def request_svtplay_kategori_page(url:str):
    try:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Microsoft Edge\";v=\"132\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0"
        }
        params = {
            "tab": "all"
        }
        response = requests.get(url, headers=headers, cookies=None, params=params)

        print(f"request_svtplay_kategori_page > response.status_code: {response.status_code}")
        if response.status_code != 200:
            raise Exception(f"request_svtplay_kategori_page failed, status_code: {response.status_code}")
        # print(f"request_svtplay_kategori_page > response.text: {response.text}")
        # dump_info(response.text, r"doc\request_svtplay_kategori_page-response_example.txt")
        return response
        
        # 获取视频url
        # headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"}
        # base_url = "https://www.svtplay.se"

        # response = requests.get(url, headers=headers)
        # if response.status_code != 200:
        #     raise Exception(f"{url}请求失败，状态码：{response.status_code}")
        # 解析mp4链接
        # sub_video_url = tree.xpath('//*[@id="play_main-content"]/div/div[1]/div[2]/div/div/div/a[1]/@href')
        # video_url = f"{base_url}{sub_video_url[0]}"
        # print(f"视频链接：{video_url}")
        # 下载
        # download_video_yt_dlp(video_url)

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")

def parse_svtplay_kategori_page(html:str):
    from lxml import etree
    """
    从HTML内容中提取data-css-selector="contentItemLink"的href值。
    
    参数:
        html_content (str): HTML内容的字符串。
    
    返回:
        list: 所有匹配的href值。
    """
    parser = etree.HTMLParser()
    tree = etree.fromstring(html, parser)
    origin_hrefs = []
    # 提取href值
    # elements_1 = tree.xpath('//a[@data-css-selector="contentItemLink"]')
    # origin_hrefs += [element.get('href') for element in elements_1]
    # elements_2 = tree.xpath('//a[@data-rt="associated-header-link"]')
    # origin_hrefs += [element.get('href') for element in elements_2]
    elements_a = tree.xpath('//a')
    origin_hrefs += [element.get('href') for element in elements_a]
    # print(hrefs)
    # 清洗href
    res_hrefs = []
    for href in origin_hrefs:
        ele = href.split("/")
        if len(ele) >= 4 and ele[1] == "video":
            res_hrefs.append(href)
    # print(res_hrefs)
    return res_hrefs

if __name__ == '__main__':
    request_video_info_api("https://www.svtplay.se/video/jNgQ3XK/varldens-starkaste-bella")


    