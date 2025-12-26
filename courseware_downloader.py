"""
课件下载模块
"""
import os
import re
import json
from typing import List, Dict, Optional


class CoursewareDownloader:
    """课件下载器"""
    
    def __init__(self, session, download_path: str = "./downloads"):
        """
        初始化下载器
        :param session: requests会话
        :param download_path: 下载路径
        """
        self.session = session
        self.download_path = download_path
        
        # 从session的cookies中提取bili_jct（CSRF token）
        self.csrf = None
        for cookie in session.cookies:
            if cookie.name == 'bili_jct':
                self.csrf = cookie.value
                break
    
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        :param filename: 原始文件名
        :return: 清理后的文件名
        """
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        filename = filename.strip()
        if len(filename) > 200:
            filename = filename[:200]
        return filename
    
    def get_courseware_url(self, file_id: int, season_id: int = None) -> Optional[Dict]:
        """
        获取课件下载地址
        :param file_id: 课件文件ID
        :param season_id: 课程ID（必需）
        :return: 课件信息（包含URL或网盘链接）
        """
        if not self.csrf:
            print("  ⚠️ 缺少CSRF token (bili_jct)")
            return None
        
        if not season_id:
            print("  ⚠️ 缺少课程ID (season_id)")
            return None
        
        try:
            # 使用真实的课件下载API
            api_url = f"https://api.bilibili.com/pugv/app/web/course/download?csrf={self.csrf}"
            
            # POST数据（必须包含season_id）
            data = f'file_id={file_id}&season_id={season_id}&section_id=0&episode_id=0&csrf={self.csrf}&csource='
            
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': 'https://www.bilibili.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = self.session.post(api_url, data=data, headers=headers, timeout=10)
            
            # 检查状态码
            if response.status_code != 200:
                print(f"  ⚠️ API返回状态码: {response.status_code}")
                return None
            
            # 解析JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                print(f"  ⚠️ API返回非JSON: {response.text[:200]}")
                return None
            
            if result.get('code') == 0:
                data = result.get('data')
                if not data:
                    print(f"  ⚠️ API返回成功但无数据")
                    return None
                
                # 判断返回的数据类型
                if isinstance(data, str):
                    # 直接返回URL字符串
                    if data.startswith('http'):
                        print(f"  ✓ 成功获取课件下载链接")
                        return {'url': data, 'type': 1}  # type 1 表示直接下载
                    else:
                        print(f"  ⚠️ 返回数据格式异常: {data[:100]}")
                        return None
                        
                elif isinstance(data, dict):
                    # 返回对象，可能包含网盘信息
                    # 检查是否有直接下载链接
                    if 'url' in data or 'download_url' in data:
                        url = data.get('url') or data.get('download_url')
                        print(f"  ✓ 成功获取课件下载链接")
                        return {'url': url, 'type': 1}
                    
                    # 检查是否有网盘链接
                    elif 'link' in data or 'netdisk' in data:
                        print(f"  ✓ 成功获取网盘链接信息")
                        netdisk_info = data.get('netdisk', data)
                        return {
                            'type': 2,
                            'netdisk': {
                                'link': netdisk_info.get('link', ''),
                                'password': netdisk_info.get('password', ''),
                                'type': netdisk_info.get('type', '网盘')
                            }
                        }
                    else:
                        print(f"  ℹ️ 返回其他类型数据")
                        return {'type': 0, 'raw_data': data}
                else:
                    print(f"  ⚠️ 未知的数据类型: {type(data)}")
                    return None
            else:
                message = result.get('message', '未知错误')
                print(f"  ⚠️ API返回错误: {message}")
                return None
                    
        except Exception as e:
            print(f"  ⚠️ 获取课件URL失败: {e}")
            return None
    
    def download_courseware(self, course_path: str, courseware_list: List[Dict], season_id: int = None) -> int:
        """
        下载课程的所有课件
        :param course_path: 课程目录
        :param courseware_list: 课件列表
        :param season_id: 课程ID
        :return: 成功下载数量
        """
        if not courseware_list:
            return 0
        
        # 创建课件目录
        courseware_dir = os.path.join(course_path, "课件")
        os.makedirs(courseware_dir, exist_ok=True)
        
        success_count = 0
        
        for idx, courseware in enumerate(courseware_list, 1):
            file_id = courseware.get('file_id')
            file_name = courseware.get('file_name', f'课件{idx}')
            
            print(f"\n[{idx}/{len(courseware_list)}] 正在处理课件: {file_name}")
            
            if not file_id:
                print("  ⚠️ 缺少课件ID，跳过")
                continue
            
            # 获取课件详情，必须传递season_id
            file_info = self.get_courseware_url(file_id, season_id)
            
            if not file_info:
                # API失败，保存课件信息供手动下载
                self._save_manual_download_info(courseware_dir, file_name, file_id, season_id)
                print("  ℹ️ 已保存课件信息，请稍后在浏览器中手动下载")
                continue
            
            # 判断课件类型
            file_type = file_info.get('type', 0)
            
            if file_type == 1:  # 直接下载链接
                download_url = file_info.get('url')
                if download_url:
                    success = self._download_direct_file(
                        download_url, 
                        courseware_dir, 
                        file_name
                    )
                    if success:
                        success_count += 1
                else:
                    print("  ⚠️ 未找到下载链接")
                    
            elif file_type == 2:  # 网盘链接
                netdisk_info = file_info.get('netdisk', {})
                self._save_netdisk_link(
                    netdisk_info, 
                    courseware_dir, 
                    file_name
                )
                success_count += 1
                
            else:
                # 尝试提取任何可能的URL
                self._extract_and_save_info(file_info, courseware_dir, file_name)
                success_count += 1
        
        return success_count
    
    def _download_direct_file(self, url: str, save_dir: str, filename: str) -> bool:
        """
        下载直接链接的文件
        :param url: 文件URL
        :param save_dir: 保存目录
        :param filename: 文件名
        :return: 是否成功
        """
        try:
            # 确定文件扩展名
            if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.zip', '.rar', '.ppt', '.pptx']):
                # 尝试从URL获取扩展名
                if '.pdf' in url.lower():
                    filename += '.pdf'
                elif '.zip' in url.lower():
                    filename += '.zip'
                elif '.doc' in url.lower():
                    filename += '.doc'
            
            safe_filename = self.sanitize_filename(filename)
            filepath = os.path.join(save_dir, safe_filename)
            
            # 检查是否已存在
            if os.path.exists(filepath):
                print(f"  ✓ 文件已存在: {safe_filename}")
                return True
            
            print(f"  📥 下载中: {safe_filename}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
            
            response = self.session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r  进度: {percent:.1f}% ({downloaded}/{total_size})", end='')
            
            print(f"\n  ✓ 下载成功: {safe_filename}")
            return True
            
        except Exception as e:
            print(f"\n  ✗ 下载失败: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return False
    
    def _save_netdisk_link(self, netdisk_info: Dict, save_dir: str, filename: str):
        """
        保存网盘链接信息
        :param netdisk_info: 网盘信息
        :param save_dir: 保存目录
        :param filename: 文件名
        """
        safe_filename = self.sanitize_filename(filename)
        txt_file = os.path.join(save_dir, f"{safe_filename}_网盘链接.txt")
        
        link = netdisk_info.get('link', '')
        password = netdisk_info.get('password', '')
        netdisk_type = netdisk_info.get('type', '网盘')
        
        content = f"课件名称: {filename}\n"
        content += f"网盘类型: {netdisk_type}\n"
        content += f"网盘链接: {link}\n"
        if password:
            content += f"提取码: {password}\n"
        content += f"\n请手动下载课件文件\n"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ 网盘链接已保存: {safe_filename}_网盘链接.txt")
        print(f"    链接: {link}")
        if password:
            print(f"    提取码: {password}")
    
    def _save_manual_download_info(self, save_dir: str, filename: str, file_id: int, season_id: int = None):
        """
        保存课件手动下载说明
        :param save_dir: 保存目录
        :param filename: 文件名
        :param file_id: 课件ID
        :param season_id: 课程ID
        """
        safe_filename = self.sanitize_filename(filename)
        txt_file = os.path.join(save_dir, f"{safe_filename}_手动下载.txt")
        
        content = f"课件名称: {filename}\n"
        content += f"课件ID: {file_id}\n"
        if season_id:
            content += f"课程ID: {season_id}\n"
            content += f"\n手动下载方法:\n"
            content += f"1. 在浏览器中访问: https://www.bilibili.com/cheese/play/ss{season_id}\n"
        else:
            content += f"\n手动下载方法:\n"
            content += f"1. 在浏览器中访问课程页面\n"
        content += f"2. 找到课件下载按钮（可能标注为'附赠课件'或'点击下载'）\n"
        content += f"3. 点击下载或复制网盘链接\n"
        content += f"\n提示: B站课程API可能不支持程序化下载课件，需要手动操作\n"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _extract_and_save_info(self, file_info: Dict, save_dir: str, filename: str):
        """
        提取并保存课件信息
        :param file_info: 课件信息
        :param save_dir: 保存目录
        :param filename: 文件名
        """
        safe_filename = self.sanitize_filename(filename)
        json_file = os.path.join(save_dir, f"{safe_filename}_info.json")
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(file_info, f, ensure_ascii=False, indent=2)
        
        print(f"  ℹ️ 课件信息已保存: {safe_filename}_info.json")
        
        # 尝试提取URL
        url = file_info.get('url') or file_info.get('download_url') or file_info.get('link')
        if url:
            print(f"    下载链接: {url}")
            # 尝试下载
            self._download_direct_file(url, save_dir, filename)
