"""
浏览器辅助工具 - 用于获取Cookie和分析API
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
import time
import os
import subprocess
import re
import platform


def get_chrome_version():
    """获取本地Chrome浏览器版本"""
    try:
        if platform.system() == "Windows":
            # Windows下常见的Chrome安装路径
            possible_paths = [
                os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]
            
            chrome_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            if chrome_path:
                # 通过注册表或文件版本获取版本号
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    return version
                except:
                    pass
                
                # 备用方法：通过wmic获取版本
                try:
                    output = subprocess.check_output(
                        f'wmic datafile where name="{chrome_path.replace(chr(92), chr(92)+chr(92))}" get Version /value',
                        shell=True, stderr=subprocess.DEVNULL
                    ).decode('utf-8', errors='ignore')
                    match = re.search(r'Version=(\d+\.\d+\.\d+\.\d+)', output)
                    if match:
                        return match.group(1)
                except:
                    pass
        else:
            # Linux/Mac
            try:
                output = subprocess.check_output(['google-chrome', '--version'], stderr=subprocess.DEVNULL).decode()
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', output)
                if match:
                    return match.group(1)
            except:
                pass
    except Exception as e:
        print(f"获取Chrome版本失败: {e}")
    return None


def download_chromedriver_from_mirror(version):
    """从国内镜像下载ChromeDriver"""
    import urllib.request
    import zipfile
    import io
    
    major_version = version.split('.')[0]
    
    # 国内镜像源
    mirrors = [
        f"https://registry.npmmirror.com/-/binary/chromedriver/{version}/chromedriver_win32.zip",
        f"https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win32/chromedriver-win32.zip",
        f"https://cdn.npmmirror.com/binaries/chromedriver/{version}/chromedriver_win32.zip",
    ]
    
    # 对于新版Chrome (115+)，使用新的下载路径
    if int(major_version) >= 115:
        mirrors = [
            f"https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win32/chromedriver-win32.zip",
            f"https://registry.npmmirror.com/-/binary/chrome-for-testing/{version}/win64/chromedriver-win64.zip",
        ]
    
    driver_dir = os.path.join(os.path.dirname(__file__), "drivers")
    os.makedirs(driver_dir, exist_ok=True)
    driver_path = os.path.join(driver_dir, "chromedriver.exe")
    
    if os.path.exists(driver_path):
        print(f"使用已缓存的ChromeDriver: {driver_path}")
        return driver_path
    
    for mirror_url in mirrors:
        try:
            print(f"正在从镜像下载ChromeDriver: {mirror_url}")
            req = urllib.request.Request(mirror_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=30)
            zip_data = response.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for name in zf.namelist():
                    if name.endswith('chromedriver.exe'):
                        with zf.open(name) as src:
                            with open(driver_path, 'wb') as dst:
                                dst.write(src.read())
                        print(f"ChromeDriver已下载到: {driver_path}")
                        return driver_path
        except Exception as e:
            print(f"镜像 {mirror_url} 下载失败: {e}")
            continue
    
    return None


def get_chromedriver_path():
    """获取ChromeDriver路径，支持多种方式"""
    
    # 方式1：检查本地drivers目录
    local_driver = os.path.join(os.path.dirname(__file__), "drivers", "chromedriver.exe")
    if os.path.exists(local_driver):
        print(f"使用本地ChromeDriver: {local_driver}")
        return local_driver
    
    # 方式2：检查环境变量中的chromedriver
    try:
        result = subprocess.run(['where', 'chromedriver'], capture_output=True, text=True)
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            print(f"使用环境变量中的ChromeDriver: {path}")
            return path
    except:
        pass
    
    # 方式3：尝试从国内镜像下载
    chrome_version = get_chrome_version()
    if chrome_version:
        print(f"检测到Chrome版本: {chrome_version}")
        driver_path = download_chromedriver_from_mirror(chrome_version)
        if driver_path:
            return driver_path
    
    # 方式4：尝试使用webdriver-manager（可能因网络问题失败）
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("尝试使用webdriver-manager下载...")
        return ChromeDriverManager().install()
    except Exception as e:
        print(f"webdriver-manager下载失败: {e}")
    
    return None


class BilibiliHelper:
    """B站浏览器辅助工具"""
    
    def __init__(self):
        """初始化浏览器"""
        print("正在启动浏览器...")
        
        # 配置Chrome选项
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 如果需要无头模式可以取消注释
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 启用网络日志
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            # 获取ChromeDriver路径
            driver_path = get_chromedriver_path()
            
            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # 最后尝试让Selenium自动查找
                print("尝试让Selenium自动查找ChromeDriver...")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            self.driver.execute_cdp_cmd('Network.enable', {})
            print("浏览器启动成功！")
        except Exception as e:
            print(f"启动浏览器失败: {e}")
            print("\n" + "="*60)
            print("解决方案：")
            print("1. 确保已安装Chrome浏览器")
            print("2. 手动下载ChromeDriver:")
            print("   - 访问 https://googlechromelabs.github.io/chrome-for-testing/")
            print("   - 下载与你Chrome版本匹配的chromedriver")
            print("   - 解压后将chromedriver.exe放到本项目的 drivers 文件夹中")
            print("="*60)
            raise
    
    def open_course_page(self):
        """打开课程页面"""
        print("\n正在打开B站课程页面...")
        self.driver.get('https://www.bilibili.com/cheese/mine/list')
        print("页面已打开！")
        print("\n" + "="*60)
        print("请在浏览器中完成登录操作")
        print("登录完成后，在终端输入 'y' 并回车继续")
        print("="*60 + "\n")
    
    def wait_for_login(self):
        """等待用户登录"""
        print("等待30秒让你完成登录...")
        time.sleep(30)
        print("\n检查登录状态...")
        
        # 检查是否登录成功
        try:
            # 尝试获取用户信息
            cookies = self.driver.get_cookies()
            sessdata = None
            for cookie in cookies:
                if cookie['name'] == 'SESSDATA':
                    sessdata = cookie['value']
                    break
            
            if sessdata:
                print("✓ 检测到登录状态")
                return True
            else:
                print("✗ 未检测到登录信息，请确保已登录")
                return False
        except:
            print("✗ 检查登录状态失败")
            return False
    
    def get_cookies(self):
        """获取所有Cookie"""
        cookies = self.driver.get_cookies()
        
        print("\n" + "="*60)
        print("Cookie信息：")
        print("="*60)
        
        # 转换为字符串格式
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        print(f"\n完整Cookie字符串：")
        print(cookie_str[:200] + "..." if len(cookie_str) > 200 else cookie_str)
        
        # 保存关键Cookie
        important_cookies = {}
        for cookie in cookies:
            if cookie['name'] in ['SESSDATA', 'bili_jct', 'buvid3', 'DedeUserID']:
                important_cookies[cookie['name']] = cookie['value']
                print(f"\n{cookie['name']}: {cookie['value']}")
        
        return cookie_str, important_cookies
    
    def capture_api_requests(self, duration=10):
        """捕获API请求"""
        print(f"\n正在监听API请求（{duration}秒）...")
        print("请在浏览器中刷新页面或进行操作...")
        
        # 刷新页面以触发API请求
        self.driver.refresh()
        time.sleep(duration)
        
        # 获取性能日志
        logs = self.driver.get_log('performance')
        
        api_requests = []
        for entry in logs:
            log = json.loads(entry['message'])['message']
            
            # 只关注网络请求
            if log['method'] == 'Network.responseReceived':
                response = log['params']['response']
                url = response['url']
                
                # 筛选B站API
                if 'api.bilibili.com' in url and 'pugv' in url:
                    api_requests.append({
                        'url': url,
                        'status': response['status'],
                        'method': response.get('method', 'GET')
                    })
        
        print(f"\n找到 {len(api_requests)} 个相关API请求：")
        print("="*60)
        
        seen_urls = set()
        for req in api_requests:
            # 去重
            if req['url'] not in seen_urls:
                seen_urls.add(req['url'])
                print(f"\nURL: {req['url']}")
                print(f"状态: {req['status']}")
                print(f"方法: {req['method']}")
        
        return api_requests
    
    def save_config(self, cookie_str):
        """保存配置"""
        config = {
            "cookie": cookie_str,
            "download_path": "./downloads"
        }
        
        config_path = "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 配置已保存到 {config_path}")
    
    def close(self):
        """关闭浏览器"""
        print("\n关闭浏览器...")
        self.driver.quit()
        print("完成！")


def main():
    """主函数"""
    helper = None
    try:
        # 创建辅助工具
        helper = BilibiliHelper()
        
        # 打开课程页面
        helper.open_course_page()
        
        # 等待登录
        if not helper.wait_for_login():
            print("\n请重新运行脚本并完成登录")
            return
        
        # 获取Cookie
        cookie_str, important_cookies = helper.get_cookies()
        
        # 捕获API请求
        api_requests = helper.capture_api_requests(duration=5)
        
        # 保存配置
        helper.save_config(cookie_str)
        
        print("\n" + "="*60)
        print("分析完成！")
        print("="*60)
        print("\n下一步：运行 'python main.py' 开始下载课程")
        
        # 询问是否关闭浏览器
        print("\n浏览器将保持打开，你可以继续查看。")
        input("按回车键关闭浏览器...")
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if helper:
            helper.close()


if __name__ == "__main__":
    main()
