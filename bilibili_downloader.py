"""
B站视频下载模块
"""
import requests
import os
import re
from typing import Dict, Optional
from pathlib import Path
import time


class BilibiliDownloader:
    """B站视频下载器"""
    
    def __init__(self, session: requests.Session, download_path: str = "./downloads"):
        """
        初始化下载器
        :param session: requests会话
        :param download_path: 下载路径
        """
        self.session = session
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        :param filename: 原始文件名
        :return: 清理后的文件名
        """
        # 移除Windows文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        # 移除前后空格
        filename = filename.strip()
        # 限制文件名长度
        if len(filename) > 200:
            filename = filename[:200]
        return filename
    
    def download_file(self, url: str, filepath: str, headers: Optional[Dict] = None) -> bool:
        """
        下载文件
        :param url: 文件URL
        :param filepath: 保存路径
        :param headers: 请求头
        :return: 是否成功
        """
        try:
            if headers is None:
                headers = {}
            
            # 合并默认headers
            download_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
            download_headers.update(headers)
            
            response = self.session.get(url, headers=download_headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size})", end='')
            
            print()  # 换行
            return True
            
        except Exception as e:
            print(f"\n下载失败: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return False
    
    def download_video_dash(self, playurl_data: Dict, output_path: str, title: str) -> bool:
        """
        下载DASH格式视频（视频和音频分离）
        :param playurl_data: 播放地址数据
        :param output_path: 输出路径
        :param title: 视频标题
        :return: 是否成功
        """
        try:
            dash = playurl_data.get('dash')
            if not dash:
                print("未找到DASH格式视频")
                return False
            
            # 获取最高质量的视频流（列表中第一个通常是最高画质）
            video_list = dash.get('video', [])
            if not video_list:
                print("未找到视频流")
                return False
            video = video_list[0]
            print(f"视频画质: {video.get('id', 'unknown')} - {video.get('width', 0)}x{video.get('height', 0)}")
            
            # 获取音频流
            audio_list = dash.get('audio', [])
            if not audio_list:
                print("错误: 未找到音频流，无法下载完整视频")
                return False
            audio = audio_list[0]
            
            # 尝试不同的URL字段名
            video_url = video.get('baseUrl') or video.get('base_url') or video.get('url')
            audio_url = audio.get('baseUrl') or audio.get('base_url') or audio.get('url')
            
            if not video_url or not audio_url:
                print(f"错误: 无法获取视频URL")
                print(f"视频数据: {video}")
                print(f"音频数据: {audio}")
                return False
            
            safe_title = self.sanitize_filename(title)
            video_file = os.path.join(output_path, f"{safe_title}_video.m4s")
            audio_file = os.path.join(output_path, f"{safe_title}_audio.m4s")
            output_file = os.path.join(output_path, f"{safe_title}.mp4")
            
            # 如果已存在，跳过
            if os.path.exists(output_file):
                print(f"文件已存在，跳过: {output_file}")
                return True
            
            print(f"\n下载视频流...")
            if not self.download_file(video_url, video_file):
                return False
            
            print(f"下载音频流...")
            if not self.download_file(audio_url, audio_file):
                # 清理已下载的视频文件
                if os.path.exists(video_file):
                    os.remove(video_file)
                return False
            
            # 合并视频和音频
            print("合并视频和音频...")
            try:
                success = self.merge_video_audio(video_file, audio_file, output_file)
                
                # 删除临时文件
                if os.path.exists(video_file):
                    os.remove(video_file)
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                
                return success
            except Exception as e:
                # 合并失败，清理临时文件
                print(f"合并失败，清理临时文件...")
                if os.path.exists(video_file):
                    os.remove(video_file)
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                return False
                
        except Exception as e:
            print(f"下载视频失败: {e}")
            return False
    
    def merge_video_audio(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """
        使用ffmpeg合并视频和音频
        :param video_path: 视频文件路径
        :param audio_path: 音频文件路径
        :param output_path: 输出文件路径
        :return: 是否成功
        """
        try:
            import subprocess
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c', 'copy',
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("合并成功!")
                return True
            else:
                print(f"合并失败: {result.stderr}")
                raise Exception(f"ffmpeg合并失败，返回码: {result.returncode}")
                
        except FileNotFoundError:
            print("错误: 未找到ffmpeg，请确保ffmpeg已安装并添加到系统PATH")
            raise Exception("ffmpeg未安装或未添加到PATH")
        except Exception as e:
            print(f"合并出错: {e}")
            raise
    
    def download_episode(self, episode: Dict, course_path: str, index: int) -> bool:
        """
        下载单个课程剧集
        :param episode: 剧集信息
        :param course_path: 课程目录
        :param index: 剧集序号
        :return: 是否成功
        """
        from bilibili_course import BilibiliCourse
        
        ep_id = episode.get('id')
        cid = episode.get('cid')
        title = episode.get('title', f'第{index}集')
        
        print(f"\n{'='*60}")
        print(f"准备下载: {index:02d}. {title}")
        print(f"{'='*60}")
        
        # 创建课程对象以获取播放地址
        from bilibili_auth import BilibiliAuth
        auth = BilibiliAuth()
        course = BilibiliCourse(auth)
        
        playurl_data = course.get_episode_playurl(ep_id, cid)
        if not playurl_data:
            print("获取播放地址失败")
            return False
        
        filename = f"{index:02d}. {title}"
        
        return self.download_video_dash(playurl_data, course_path, filename)
