def get_cloud_save_path_by_language(save_path:str, lang_key:str)->str:
    ''' 
    语言对应的云存储路径
    :param save_path: 保存的云存储路径
    :param lang_key: 语言key
    :return: language 对应的云存储路径
    '''
    ret_path = str("")   
    LANGUAGE_PATH_DICT = {
        "ar": "Alaboyu",		# 阿拉伯语
		"bo": "Zangyu",			# 藏语
        "de": "Deyu",			# 德语
        "el": "Xilayu/modern",	# 现代希腊语
        "en": "English",		# 英语
        "es": "Xibanyayu",		# 西班牙语
        "fil": "Feilvbinyu",	# 菲律宾语
        "fr": "Fayu",			# 法语
        "id": "Yinniyu",		# 印尼语
		"it": "Yidaliyu",		# 意大利语
        "ja": "Riyu",			# 日语
        "ko": "Hanyu",			# 韩语
        "ms": "Malaiyu",		# 马来语
        "nan": "Minnanyu",		# 闽南语
		"pl": "Bolanyu",		# 波兰语
		"pt": "Putaoyayu",		# 葡萄牙语
        "ru": "Eyu",			# 俄语
        "th": "Taiyu",			# 泰语
        "vi": "Vietnam",		# 越南语
        "yue": "Yueyu",			# 粤语
        "zh": "Zhongwen",		# 中文
        "nl": "language/Helanyu",       # 荷兰语
        "hi": "language/Yindiyu",       # 印地语
        "tr": "language/Tuerqiyu",      # 土耳其语
        "sv": "language/Ruidianyu",     # 瑞典语
        "bg": "language/Baojialiyayu",  # 保加利亚语
        "ro": "language/Luomaniyayu",   # 罗马尼亚语
        "cs": "language/Jiekeyu",       # 捷克语
        "fi": "language/Fenlanyu",      # 芬兰语
        "hr": "language/Keluodiyayu",   # 克罗地亚语
        "sk": "language/Siluofakeyu",   # 斯洛伐克
        "da": "language/Danmaiyu",      # 丹麦语
        "ta": "language/Taimieryu",     # 泰米尔语
        "uk": "language/Wukelanyu",     # 乌克兰语
        "tl": "language/Tajialuyu",		# 他加禄语
        "mn": "language/Mengguyu",		# 蒙语/蒙古语
        "bo": "language/Zangyu",		# 藏语
        "ug": "language/Weiwueryu",		# 维语/维吾尔语
        "test": f"Unclassify/test",             # 测试数据
        "unknown": f"Unclassify/{lang_key}",    # 其他
    }
    if "{LANGUAGE}" in save_path:
        ret_path = save_path.format(LANGUAGE=LANGUAGE_PATH_DICT.get(lang_key.lower(), f"Unclassify/{lang_key}"))
    else:
        ret_path = save_path
    
    return ret_path
