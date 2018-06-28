from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client

from dailyfresh import settings


class FastDFSStorage(Storage):

    def __init__(self, client_conf=None, server_ip=None):
        # 可以自定义fdfs的ip地址和客户端参数文件，可以不定义，使用默认值
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if server_ip is None:
            server_ip = settings.FDFS_SERVER_IP
        self.server_ip = server_ip

    # 访问文件的时候执行的方法
    def _open(self):

        pass

    # 存储图片执行的方法
    def _save(self, name, content):
        # name是图片的原始名字，content是传过来的图片对象

        # 生成fdfs对象，用来访问fdfs服务器
        client = Fdfs_client(self.client_conf)
        # 读取图片文件
        file_data = content.read()
        # 上传图片到fastdfs
        try:
            # 上传图片需要访问fdfs服务，是远程链接，也有可能出现异常
            ret = client.upload_by_buffer(file_data)
        except Exception as e:
            print(e)
            raise
        """ ret返回下面这种类型的值
        {
            'Group name': 'group1',
            'Status': 'Upload successed.',  # 注意这有一个点
            'Remote file_id': 'group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py',
            'Uploaded size': '6.0KB',
            'Local file name': 'test',
            'Storage IP': '192.168.243.133'
        }
        """
        # 判断是否上传成功,获取文件的存放的真是路径和名字
        if ret.get('Status') == 'Upload successed.':
            file_id = ret.get('Remote file_id')
            return file_id
        else:
            # 抛出异常
            raise Exception('上传图片到fdfs失败')

    # 由于Djnago不存储图片，所以永远返回Fasle，直接引导到FastFDS
    def exists(self, name):

        return False

    # 返回存储在fdfs的图片地址
    def url(self, name):
        # name: group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py
        # <img src='http://192.168.217.136:8888/group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py'>
        return self.server_ip + name

