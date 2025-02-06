import requests
import json
from os import getenv, path
from utils.request import download_resource
from utils.file import dump_info
from utils.lark import alarm, alarm_lark_text
from utils.logger import logger
from utils.utime import get_time_stamp
from database.crawler_audio_download_info import Audio, request_update_audio_api

_PROXIES = {'http': getenv("HTTP_PROXY"),'https': getenv("HTTP_PROXY")} if getenv("HTTP_PROXY", "") != "" else None

def get_address_location():
    """
    Gets the current location information from Yle's API.

    :return: The response object of the request.
    """
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://areena.yle.fi",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://areena.yle.fi/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    url = "https://locations.api.yle.fi/v3/address/current"
    params = {
        "app_id": "areena-web-items",
        "app_key": "wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN"
    }
    response = requests.get(url, headers=headers, params=params)

    print(f"get_address_location > response.text: {response.status_code}")
    print(f"get_address_location > response.text: {response.text}")
    '''example
        {"country_code":"US","continent":"NA","asnum":"49791","is_portability_region":false}
        {"country_code":"HK","continent":"AS","asnum":"202662","is_portability_region": false}
    '''

def request_podcastit_preview_api(url:str):
    '''
    input: https://areena.yle.fi/podcastit/1-72758068
    request: https://player.api.yle.fi/v1/preview/1-72758068.json
    '''
    # 转换url为实际请求url
    url = "https://player.api.yle.fi/v1/preview/" + url.split("podcastit/")[-1] + ".json"

    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://areena.yle.fi",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://areena.yle.fi/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    cookies = {
        "yle_selva": "17374443029914105106",
        "AMCVS_3D717B335952EB220A495D55%40AdobeOrg": "1",
        "AMCV_3D717B335952EB220A495D55%40AdobeOrg": "1585540135%7CMCMID%7C65600694663927198692694376961486283411%7CMCAAMLH-1738049132%7C3%7CMCAAMB-1738049132%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1737451532s%7CNONE%7CvVersion%7C4.4.0",
        "s_cc": "true",
        "userconsent": "v2|development|embedded_social_media",
        "yle_rec": "1737444336098920023149",
        "_cb": "gEHERDN5C8NBXgqzk",
        "_chartbeat2": ".1737444338045.1737444338045.1.BjgXOUG2w-8XRGiSFrh9SCQ6rPy.1",
        "areena_ab": "aa0%2CpackageEAS1%2CpersonalCMF1%2CsimilarityRIEC1"
    }
    # url = "https://player.api.yle.fi/v1/preview/1-73010670.json"
    params = {
        "app_id": "player_static_prod",
        "app_key": "8930d72170e48303cf5f3867780d549b",
        "language": "fin",
        "host": "areenaylefi",
        "isMobile": "false",
        "ssl": "true",
        "countryCode": "US",
        "isPortabilityRegion": "false",
    }
    response = requests.get(url, headers=headers, cookies=cookies, params=params, proxies=_PROXIES)

    print(f"request_podcastit_preview_api > response.status_code: {response.status_code}")
    if response.status_code != 200:
        raise requests.RequestException(f"request_podcastit_preview_api status_code: {response.status_code}")
    print(f"request_podcastit_preview_api > response.text: {response.text}")
    return response

def parse_podcastit_preview_response(response:requests.Response):
    data_json = response.json()
    media_url = data_json["data"]["ongoing_ondemand"]["media_url"]
    media_info = data_json["data"]["ongoing_ondemand"]
    return media_url, media_info

def update_audio_with_media_info(audio:Audio, media_info:dict={}):
    if not media_info:
        return
    try:
        # audio.duration
        try:
            audio.duration = media_info.get("duration").get("duration_in_seconds")
        except Exception as err:
            logger.warning(f"update_audio_with_media_info > {audio.vid} get audio duraion failed, {err}")

        # audio.info
        result_dict = {}
        if audio.info in [None, "", "{}"]:
            result_dict = media_info
        else:
            audio_info = json.loads(audio.info)
            result_dict = audio_info | media_info # Python3.9+
        audio.info = json.dumps(result_dict)

        # update
        request_update_audio_api(
            url="%s?sign=%d"%(getenv("DATABASE_AUDIO_UPDATE_API"), get_time_stamp()), 
            audio=audio,
        )
    except Exception as e:
        logger.warning(f"update_audio_with_media_info > {audio.vid} update failed, {e}")
        return

def request_podcastit_list_api(url:str="https://areena.api.yle.fi/v1/ui/content/list", page:int=1, page_size:int=16, token=""):
    print(f"request_podcastit_list_api > params url:{url} | page:{page} | page_size:{page_size}")
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://areena.yle.fi",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://areena.yle.fi/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    cookies = {
        "yle_selva": "17374443029914105106",
        "userconsent": "v2|development|embedded_social_media",
        "yle_rec": "1737444336098920023149",
        "_cb": "gEHERDN5C8NBXgqzk",
        "areena_ab": "aa0%2CpackageEAS1%2CpersonalCMF1%2CsimilarityRIEC1",
        "_cb_svref": "null",
        "AMCVS_3D717B335952EB220A495D55%40AdobeOrg": "1",
        "AMCV_3D717B335952EB220A495D55%40AdobeOrg": "1585540135%7CMCMID%7C65600694663927198692694376961486283411%7CMCAAMLH-1738307382%7C7%7CMCAAMB-1738307382%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1737709782s%7CNONE%7CvVersion%7C4.4.0",
        "s_cc": "true",
        "_chartbeat2": ".1737444338045.1737702614425.1011.BIPAzTCdSm82sVO26WBnJ4B6kCFW.2",
        "_chartbeat5": "234|1685|%2Fpodcastit|https%3A%2F%2Fareena.yle.fi%2Fpodcastit%2Fohjelmat%2F30-3120|CjJMfg21uUwOspeIDLdoQFC_-nRE||c|CSyicvDUL9ogCWW12GCzLIYFBBqZdx|areena.yle.fi|",
        "yleAnalyticsLink": "%7B%22position%22%3A%22%23maincontent%20%3E%20%3Anth-child(3)%20%3E%20%3Anth-child(6)%20%3E%20%3Anth-child(1)%20%3E%20%3Anth-child(1)%20%3E%20%3Anth-child(2)%20%3E%20%3Anth-child(1)%20%3E%20%3Anth-child(1)%22%2C%22text%22%3A%22N%C3%A4yt%C3%A4%20kaikki%22%2C%22from%22%3A%22areena.yle.fi%2Fpodcastit%22%2C%22to%22%3A%22areena.yle.fi%2Fpodcastit%2Fohjelmat%2F30-3120%22%2C%22site%22%3A%22areena%22%2C%22mergeLabels%22%3Afalse%7D"
    }
    # url = "https://areena.api.yle.fi/v1/ui/content/list"
    params = {
        "client": "yle-areena-web",
        "language": "fi",
        "v": "10",
        # "token": "eyJhbGciOiJIUzI1NiJ9.eyJjYXJkT3B0aW9uc1RlbXBsYXRlIjoiY292ZXJTdHJpcCIsInNvdXJjZSI6Imh0dHBzOi8vcHJvZ3JhbXMuYXBpLnlsZS5maS92My9zY2hlbWEvdjMvcGFja2FnZXMvMzAtMTQ0L2xhdGVzdCIsImFuYWx5dGljcyI6eyJjb250ZXh0Ijp7ImNvbXNjb3JlIjp7InlsZV9yZWZlcmVyIjoicmFkaW8udmlldy41Ny01Mmx2OWFWbjAua3VsdHR1dXJpLnV1c2ltbWF0LnVudGl0bGVkX2xpc3QiLCJ5bGVfcGFja2FnZV9pZCI6IjMwLTE0NCJ9fX19.mYLkKH4JwpA2BlU0s1l9i5FFlWL-7pj8SuIEN1x8KLg",
        "token": token,
        "offset": f"{(page-1)*page_size}",
        "limit": f"{page_size}",
        # "offset": "0",
        # "limit": "16",
        "country": "US",
        "app_id": "areena-web-items",
        "app_key": "wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN"
    }
    # response = requests.get(url, headers=headers, cookies=cookies, params=params)
    response = requests.get(url, headers=headers, cookies=None, params=params, proxies=_PROXIES)

    print(f"request_podcastit_list_api > response.status_code: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"request_podcastit_list_api failed, status_code: {response.status_code}")
    print(f"request_podcastit_list_api > response.text: {response.text}")
    # dump_info(response.text, r"doc\request_podcastit_list_api-response_example.json")
    return response

def request_podcastit_search_api(query:str, url:str="https://areena.api.yle.fi/v1/ui/search", page:int=1, page_size:int=16):
    print(f"request_podcastit_search_api > params query:{query} | url:{url} | page:{page} | page_size:{page_size}")
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://areena.yle.fi",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://areena.yle.fi/",
        "sec-ch-ua": "\"Not)A;Brand\";v=\"99\", \"Google Chrome\";v=\"127\", \"Chromium\";v=\"127\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    cookies = {
        "yle_selva": "17374443029914105106",
        "userconsent": "v2|development|embedded_social_media",
        "yle_rec": "1737444336098920023149",
        "_cb": "gEHERDN5C8NBXgqzk",
        "areena_ab": "aa0%2CpackageEAS1%2CpersonalCMF1%2CsimilarityRIEC1",
        "AMCVS_3D717B335952EB220A495D55%40AdobeOrg": "1",
        "s_cc": "true",
        "_chartbeat2": ".1737444338045.1737784099758.10111.Baq4Cb9BfNcBU94_oCF0ZxGChIgpl.1",
        "_cb_svref": "https%3A%2F%2Fareena.yle.fi%2Fhae%3Fq%3DKulttuurin%26service%3Dradio",
        "AMCV_3D717B335952EB220A495D55%40AdobeOrg": "1585540135%7CMCMID%7C65600694663927198692694376961486283411%7CMCAAMLH-1738388900%7C7%7CMCAAMB-1738388900%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1737791300s%7CNONE%7CvVersion%7C4.4.0",
        "_chartbeat4": "t=Clct3XCEMmKkDA9vFzCjmT0OB2ke6n&E=12&x=1600&c=0.21&y=3032&w=953"
    }
    # url = "https://areena.api.yle.fi/v1/ui/search"
    params = {
        "language": "fi",
        "client": "yle-areena-web",
        "v": "10",
        "episodes": "true",
        "packages": "true",
        "query": "ac",
        "service": "radio",
        "offset": f"{(page-1)*page_size}",
        "limit": f"{page_size}",
        # "offset": "48",
        # "limit": "16",
        "country": "US",
        "app_id": "areena-web-items",
        "app_key": "wlTs5D9OjIdeS9krPzRQR4I1PYVzoazN"
    }
    response = requests.get(url, headers=headers, cookies=None, params=params, proxies=_PROXIES)

    print(f"request_podcastit_search_api > response.status_code: {response.status_code}")
    if response.status_code != 200:
        raise requests.RequestException(f"request_podcastit_search_api status_code: {response.status_code}")
    print(f"request_podcastit_search_api > response.text: {response.text}")
    # dump_info(response.text, r"doc\request_podcastit_list_api-response_example.json")
    return response

def parse_podcastit_list_response(response:requests.Response):
    data_json = response.json()
    # length = data_json["meta"]["count"]
    length = len(data_json["data"])
    print(f"parse_podcastit_list_response > 一共解析到{length}条数据")
    if length <= 0:
        raise ValueError("parse_podcastit_list_response解析无可用数据")
    for data in data_json["data"]:
        try:
            uri = data.get("pointer", "").get("uri", "")
            if not uri:
                raise Exception("parse uri failed")
            podcast_id = uri.split("yleareena://items/")[1]
            podcast_url = f"https://areena.yle.fi/podcastit/{podcast_id}"
        except Exception as e:
            notice_text = f"parse_podcastit_list_response > 解析失败:{e}, data:{data}"
            logger.error(notice_text)
            alarm(level="error", text=notice_text)
        else:
            yield podcast_url
        finally:
            continue

def areena_podcastit_download_handler(audio:Audio, save_path:str=""):
    if audio.source_link == "":
        raise ValueError("audio.source_link is empty")
    resp = request_podcastit_preview_api(audio.source_link)
    logger.debug(f"areena_podcastit_download_handler > {audio.vid}请求{audio.source_link}成功")
    download_url, media_info = parse_podcastit_preview_response(resp)
    logger.debug(f"areena_podcastit_download_handler > {audio.vid}解析{audio.source_link}成功")
    # 更新媒体信息
    if media_info:
        update_audio_with_media_info(audio, media_info)
        logger.debug(f"areena_podcastit_download_handler > {audio.vid}更新{audio.source_link}媒体信息成功")
    # 下载媒体文件
    if download_url == "":
        raise ValueError("download_url is empty")
    filename = path.join(save_path, f"{audio.vid}.mp3")
    download_path = download_resource(download_url, filename, _PROXIES)
    logger.debug(f"areena_podcastit_download_handler > {audio.vid}下载{audio.source_link}成功, download_path:{download_path}")
    return download_path


if __name__ == "__main__":
    # input https://areena.yle.fi/podcastit/1-73010670
    # input https://areena.yle.fi/podcastit/1-72758068
    # get_address_location()

    # 请求音频信息接口
    # https://player.api.yle.fi/v1/preview/ + 1-73010670 + .json?
    # request_podcastit_preview_api(url="https://player.api.yle.fi/v1/preview/1-73010670.json")

    # https://areena.yle.fi/podcastit/1-62939152 时长02:58 大小3.81MB
    # request_podcastit_preview_api(url="https://player.api.yle.fi/v1/preview/1-62939152.json")
    
    # https://areena.yle.fi/podcastit/1-72758068 时长02:58 大小3.81MB
    # request_podcastit_preview_api(url="https://player.api.yle.fi/v1/preview/1-72758068.json")
    '''
    {"meta":{"id":"1-72758068"},"data":{"ongoing_ondemand":{"description":{"fin":"Vieraana toimitusjohtaja Henrik Husman Nasdaq Helsingistä. Toimittajana Mikko Jylhä."},"subtitles":[],"auto_subtitles":false,"media_id":"78-c3e0d8a093c547f784a4ba9c6441b7c0","series":{"id":"1-3725092","title":{"fin":"Pörssipäivä"}},"publication_id":"4-72758069","program_id":"1-72758068","dvr_window_in_seconds":0,"cuepoints":[],"start_time":"2025-01-23T20:00:00.000+02:00","duration":{"duration_in_seconds":5215,"h":0,"m":0,"s":5215},"is_content_protected":false,"title":{"fin":"Miksi tulevat vuodet olisivat Helsingin pörssissä parempia, toimitusjohtaja Henrik Husman?"},"region":"World","content_type":"AudioObject","media_url":"https://yleawsaudioipv4.akamaized.net/aod/world/78-c3e0d8a093c547f784a4ba9c6441b7c0/audio-1737656122641.mp3?hdnts=exp=1737746407~acl=/aod/world/78-c3e0d8a093c547f784a4ba9c6441b7c0/*~hmac=bb9b8f2779e4aee4a68a8ef2a5a98c9bb62ce3e05a516af5ad8f0173e99f76d0","is_areena_visible":true,"image":{"id":"39-9190166215e3e227fa7","version":1737468434},"service_id":"yle-areena","content_rating":{"age_restriction":null,"reasons":null}}}}
    '''

    # 音频下载
    # media_url = "https://yleawsaudioipv4.akamaized.net/aod/world/78-c3e0d8a093c547f784a4ba9c6441b7c0/audio-1737656122641.mp3?hdnts=exp=1737746407~acl=/aod/world/78-c3e0d8a093c547f784a4ba9c6441b7c0/*~hmac=bb9b8f2779e4aee4a68a8ef2a5a98c9bb62ce3e05a516af5ad8f0173e99f76d0"
    # download_resource (
    #     url=media_url,
    #     filename="downloads/1-72758068.mp3",
    #     proxies=proxies
    # )

    # 请求播客列表接口
    # request_podcastit_list_api(url="https://areena.api.yle.fi/v1/ui/content/list", page=1, page_size=16)