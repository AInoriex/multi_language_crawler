from os import getenv, path
import yt_dlp

_IS_DEBUG = getenv("DEBUG", "True") == "True"
_PROXIES = getenv("HTTP_PROXY") if getenv("HTTP_PROXY") != "" else None

def download_video(url:str, filename:str):
    # 初始化yt-dlp配置
    _default_video_format = "mp4"
    ydl_opts = {
        # 通用配置
        "quiet": False if _IS_DEBUG else True, # Do not print messages to stdout.
        "verbose": True if _IS_DEBUG else False, # Print additional info to stdout.
        "proxy": _PROXIES, # 代理
        "ratelimit": 10 * 1024 * 1024, # 下载速率限制，单位MB/s
        "nooverwrites": True, # 不覆盖存在文件
        "continuedl": True, # 续传
        "noplaylist": True, # 不下载列表所有视频
        # "playlistreverse": True,
        "sleep_interval": 2, # 下载间隔
        "retries": 3, # 重试次数
        "retry_sleep_functions": {
            "http": 1,
            "fragment": 1,
            "file_access": 1,
        },
        # "paths": "downloads/", # 下载文件夹
        # "outtmpl": f"downloads/%(id)s.%(ext)s", # 下载文件名
        "outtmpl": filename, # 下载文件名
        
        # 下载格式配置
        # # 提取视频
        "format": f"bestvideo+bestaudio/best",
        "wait_for_video": "3-10",
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": _default_video_format,  # one of avi, flv, mkv, mp4, ogg, webm
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    if not path.exists(filename):
        raise Exception(f"yt-dlp 下载{filename}失败, url:{url}")
    return filename

def download_audio(url:str, filename:str):
    # 初始化yt-dlp配置
    _default_audio_format = "m4a"
    ydl_opts = {
        # 通用配置
        "quiet": False if _IS_DEBUG else True, # Do not print messages to stdout.
        "verbose": True if _IS_DEBUG else False, # Print additional info to stdout.
        "proxy": _PROXIES, # 代理
        "ratelimit": 10 * 1024 * 1024, # 下载速率限制，单位MB/s
        "nooverwrites": True, # 不覆盖存在文件
        "continuedl": True, # 续传
        "noplaylist": True, # 不下载列表所有视频
        # "playlistreverse": True, # 播放列表反转
        "sleep_interval": 2, # 下载间隔
        "retries": 3, # 重试次数
        "retry_sleep_functions": {
            "http": 1,
            "fragment": 1,
            "file_access": 1,
        },
        # "paths": "downloads/", # 下载文件夹
        # "outtmpl": f"downloads/%(id)s.%(ext)s", # 下载文件名
        "outtmpl": filename, # 下载文件名
        
        # 下载格式配置 - 提取音频
        "format": f"{_default_audio_format}/bestaudio",
        "postprocessors": [
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": _default_audio_format,
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    if not path.exists(filename):
        raise Exception(f"yt-dlp 下载{filename}失败, url:{url}")
    return filename

def download_subtitle(url:str, filename:str):
    # 初始化yt-dlp配置
    _default_subtitle_format = "srt"
    ydl_opts = {
        # 通用配置
        "quiet": False if _IS_DEBUG else True, # Do not print messages to stdout.
        "verbose": True if _IS_DEBUG else False, # Print additional info to stdout.
        "proxy": _PROXIES, # 代理
        "ratelimit": 10 * 1024 * 1024, # 下载速率限制，单位MB/s
        "nooverwrites": True, # 不覆盖存在文件
        "continuedl": True, # 续传
        "sleep_interval": 2, # 下载间隔
        "retries": 3, # 重试次数
        # "paths": "downloads/", # 下载文件夹
        # "outtmpl": f"downloads/%(id)s.%(ext)s", # 下载文件名
        "outtmpl": filename, # 下载文件名
        
        # 下载格式配置 - 提取字幕
        "skip_download": True, # 跳过音视频下载
        "writesubtitles": True, # 是否提取字幕
        "subtitleslangs": ["en"], # 提取的语言
        # "subtitlesformat": f"all/{_default_subtitle_format}", # 字幕格式
        "subtitlesformat": _default_subtitle_format,
        # "subtitle": "--write-srt --sub-lang en",
        # "listsubtitles": True, # 列出字幕
        "writeautomaticsub": True, # 自动生成vtt
        "postprocessors": [{
            "key": "FFmpegSubtitlesConvertor",
            "format": _default_subtitle_format,
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    if not path.exists(filename):
        raise Exception(f"yt-dlp 下载{filename}失败, url:{url}")
    return filename
