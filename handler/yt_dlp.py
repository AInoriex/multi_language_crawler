from os import getenv, path
import yt_dlp

def download_video(url:str, filename:str):
    # 初始化yt-dlp配置
    _is_debug = getenv("DEBUG", "True") == "True"
    _default_video_format = "mp4"
    ydl_opts = {
        # 通用配置
        "quiet": False if _is_debug else True, # Do not print messages to stdout.
        "verbose": True if _is_debug else False, # Print additional info to stdout.
        "proxy": (
            getenv("HTTP_PROXY") if getenv("HTTP_PROXY") != "" else None
        ), # 代理
        "ratelimit": 10 * 1024 * 1024, # 下载速率限制，单位MB/s
        "nooverwrites": True, # 不覆盖存在文件
        "continuedl": True, # 续传
        "noplaylist": True, # 不下载列表所有视频
        # "playlistreverse": True,
        "sleep_interval": 2, # 下载间隔
        "retries": 3,
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

        # # 提取音频
        # "format": "m4a/bestaudio/best",
        # "postprocessors": [
        #     {  # Extract audio using ffmpeg
        #         "key": "FFmpegExtractAudio",
        #         "preferredcodec": "m4a",
        #     }
        # ],

        # 提取字幕配置
        # "skip_download": True,
        # "writesubtitles": True, # 是否提取字幕
        # "subtitleslangs": ["en"], # 提取的语言
        # "subtitleslangs": [v.language],
        # "subtitlesformat": f"all/{subtitle_ext}",
        # "subtitlesformat": f"srt",
        # "subtitle": "--write-srt --sub-lang en",
        # "listsubtitles": True,
        # "writeautomaticsub": True, # 自动生成vtt
        # "postprocessors": [{
        #     "key": "FFmpegSubtitlesConvertor",
        #     "format": subtitle_ext,
        # }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(url)

    if not path.exists(filename):
        raise Exception(f"下载{filename}失败, url:{url}")
    return filename