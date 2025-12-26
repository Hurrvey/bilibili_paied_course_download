"""
B站登录和认证模块
"""
import requests
import json
import os
from typing import Dict, Optional


class BilibiliAuth:
    """B站认证类"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化认证对象
        :param config_path: 配置文件路径
        """
        self.config_path = config_path
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
        }
        self.session.headers.update(self.headers)
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            print(f"配置文件 {self.config_path} 不存在，请创建配置文件")
            return
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 设置cookie
        if 'cookie' in config and config['cookie']:
            self._parse_cookie(config['cookie'])
        else:
            # 使用单独的认证信息
            cookies = {}
            if 'SESSDATA' in config:
                cookies['SESSDATA'] = config['SESSDATA']
            if 'bili_jct' in config:
                cookies['bili_jct'] = config['bili_jct']
            if 'buvid3' in config:
                cookies['buvid3'] = config['buvid3']
            
            if cookies:
                requests.utils.add_dict_to_cookiejar(self.session.cookies, cookies)
        
        self.download_path = config.get('download_path', './downloads')
    
    def _parse_cookie(self, cookie_str: str) -> None:
        """
        解析cookie字符串
        :param cookie_str: cookie字符串
        """
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        
        requests.utils.add_dict_to_cookiejar(self.session.cookies, cookies)
    
    def check_login(self) -> bool:
        """
        检查是否已登录
        :return: 是否已登录
        """
        try:
            url = "https://api.bilibili.com/x/web-interface/nav"
            response = self.session.get(url)
            data = response.json()
            
            if data['code'] == 0 and data['data']['isLogin']:
                print(f"登录成功! 用户名: {data['data']['uname']}")
                return True
            else:
                print("未登录或cookie已失效")
                return False
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False
    
    def get_session(self) -> requests.Session:
        """
        获取会话对象
        :return: requests.Session对象
        """
        return self.session
