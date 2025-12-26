"""
B站课程获取模块
"""
import requests
import json
import os
from typing import List, Dict, Optional
from bilibili_auth import BilibiliAuth


class BilibiliCourse:
    """B站课程类"""
    
    def __init__(self, auth: BilibiliAuth):
        """
        初始化课程对象
        :param auth: 认证对象
        """
        self.auth = auth
        self.session = auth.get_session()
    
    def get_purchased_courses(self) -> List[Dict]:
        """
        获取已购买的课程列表
        :return: 课程列表
        """
        courses = []
        page = 1
        page_size = 20
        
        while True:
            try:
                # 使用正确的已购课程API
                url = "https://api.bilibili.com/pugv/pay/web/my/paid"
                params = {
                    'pn': page,
                    'ps': page_size
                }
                
                print(f"正在请求第 {page} 页...")
                response = self.session.get(url, params=params, timeout=10)
                
                print(f"HTTP状态码: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"HTTP状态码异常: {response.status_code}")
                    break
                
                data = response.json()
                print(f"API响应: {json.dumps(data, ensure_ascii=False)[:200]}")
                
                if data['code'] != 0:
                    print(f"获取课程列表失败: {data.get('message', '未知错误')}")
                    break
                
                # 从data.data中获取课程列表（注意是双层data）
                data_obj = data.get('data', {})
                items = data_obj.get('data', [])  # 注意这里是data.data
                
                if not items:
                    break
                
                # 处理每个课程，提取正确的字段
                for item in items:
                    course_info = {
                        'season_id': item.get('id') or item.get('season_id'),  # API返回的是id字段
                        'title': item.get('title'),
                        'ep_count': item.get('ep_count', 0),
                        'cover': item.get('cover', '')
                    }
                    courses.append(course_info)
                print(f"已获取 {len(courses)} 个课程...")
                
                # 检查是否还有更多页
                total = data.get('data', {}).get('total', 0)
                if len(courses) >= total or len(items) < page_size:
                    break
                
                page += 1
                
            except Exception as e:
                print(f"获取课程列表出错: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"共获取到 {len(courses)} 个已购买的课程")
        return courses
    
    def _get_courses_alternative(self) -> List[Dict]:
        """
        使用备用API获取课程列表
        :return: 课程列表
        """
        courses = []
        
        # 尝试多个可能的API
        apis_to_try = [
            {
                'url': 'https://api.bilibili.com/pugv/app/web/season/page',
                'params': {'pn': 1, 'ps': 50, 'type': 1}
            },
            {
                'url': 'https://api.bilibili.com/x/pugv/trade/order/list/all',
                'params': {'pn': 1, 'ps': 50}
            },
            {
                'url': 'https://api.bilibili.com/pugv/web/season/mine',
                'params': {}
            }
        ]
        
        for api_config in apis_to_try:
            try:
                print(f"\n尝试API: {api_config['url']}")
                response = self.session.get(
                    api_config['url'], 
                    params=api_config['params'],
                    timeout=10
                )
                print(f"HTTP状态码: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"HTTP状态码异常: {response.status_code}")
                    continue
                
                try:
                    data = response.json()
                except:
                    print(f"响应不是JSON格式")
                    continue
                    
                print(f"API响应: {json.dumps(data, ensure_ascii=False)[:300]}")
                
                if data.get('code') == 0:
                    # 尝试不同的数据结构
                    items = []
                    if 'data' in data:
                        if isinstance(data['data'], list):
                            items = data['data']
                        elif isinstance(data['data'], dict):
                            items = data['data'].get('items', data['data'].get('list', []))
                    
                    if items:
                        print(f"成功获取到 {len(items)} 个课程")
                        for item in items:
                            course_info = {
                                'season_id': item.get('season_id') or item.get('ssid'),
                                'title': item.get('title') or item.get('course_title'),
                                'ep_count': item.get('ep_count', 0),
                                'cover': item.get('cover', '')
                            }
                            if course_info['season_id']:  # 只添加有ID的课程
                                courses.append(course_info)
                        
                        if courses:
                            return courses
                else:
                    print(f"API返回错误: code={data.get('code')}, message={data.get('message')}")
                    
            except Exception as e:
                print(f"尝试API {api_config['url']} 失败: {e}")
                continue
        
        print("\n所有API尝试均失败")
        print("\n请确认：")
        print("1. 你的Cookie是否在 https://www.bilibili.com/cheese/mine/list 页面获取的")
        print("2. Cookie是否包含 SESSDATA、bili_jct、buvid3 等字段")
        print("3. 是否已经购买了课程")
        
        return courses
    
    def get_course_detail(self, season_id: int) -> Optional[Dict]:
        """
        获取课程详情
        :param season_id: 课程ID
        :return: 课程详情
        """
        try:
            url = f"https://api.bilibili.com/pugv/view/web/season"
            params = {
                'season_id': season_id
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if data['code'] != 0:
                print(f"获取课程详情失败: {data.get('message', '未知错误')}")
                return None
            
            return data['data']
            
        except Exception as e:
            print(f"获取课程详情出错: {e}")
            return None
    
    def get_episode_playurl(self, ep_id: int, cid: int) -> Optional[Dict]:
        """
        获取视频播放地址
        :param ep_id: 剧集ID
        :param cid: 视频CID
        :return: 播放地址信息
        """
        try:
            url = "https://api.bilibili.com/pugv/player/web/playurl"
            params = {
                'ep_id': ep_id,
                'cid': cid,
                'qn': 127,  # 清晰度，127表示最高画质（8K），会自动降级到可用的最高画质
                'fnval': 16,  # 格式，16表示dash格式
                'fourk': 1
            }
            
            response = self.session.get(url, params=params)
            data = response.json()
            
            if data['code'] != 0:
                print(f"获取播放地址失败: {data.get('message', '未知错误')}")
                return None
            
            return data['data']
            
        except Exception as e:
            print(f"获取播放地址出错: {e}")
            return None
    
    def list_courses_summary(self, courses: List[Dict]) -> None:
        """
        打印课程摘要
        :param courses: 课程列表
        """
        print("\n" + "="*60)
        print("已购买的课程列表:")
        print("="*60)
        
        for idx, course in enumerate(courses, 1):
            title = course.get('title', '未知课程')
            season_id = course.get('season_id', 0)
            ep_count = course.get('ep_count', 0)
            print(f"{idx}. {title} (ID: {season_id}, 共 {ep_count} 集)")
        
        print("="*60 + "\n")
