import time

class Context:
    """
    上下文类，用于保存全局变量
    """
    def __init__(self):
        self.__dict__ = {}
        self.__dict__['creat_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    # 设置上下文
    def set(self, key, value):
        self.__dict__[key] = value

    # 获取上下文
    def get(self, key):
        return self.__dict__[key]

    # 删除上下文
    def delete(self, key):
        del self.__dict__[key]
    
    # 判断key是否存在
    def has(self, key):
        return key in self.__dict__
    
    # 遍历context所有key并写入文件
    def write_to_file(self, file_path='./doc/context_output.txt'):
        with open(file_path, 'a', encoding='utf-8') as f:
            # f.write(str(self))
            for k, v in self.__dict__.items():
                f.writelines(f"{k}: {v}\n")
            f.writelines('\n\n')

    # 列举context所有key-value
    def __str__(self):
        return str(self.__dict__)
    