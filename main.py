"""
B站课程批量下载工具
"""
import os
import json
from bilibili_auth import BilibiliAuth
from bilibili_course import BilibiliCourse
from bilibili_downloader import BilibiliDownloader
from courseware_downloader import CoursewareDownloader


def main():
    """主函数"""
    print("="*60)
    print("B站课程批量下载工具")
    print("="*60)
    
    # 初始化认证
    auth = BilibiliAuth()
    
    # 检查登录状态
    if not auth.check_login():
        print("\n请先配置config.json文件中的cookie信息")
        print("获取cookie的方法:")
        print("1. 在浏览器中登录B站")
        print("2. 按F12打开开发者工具")
        print("3. 切换到Network标签")
        print("4. 刷新页面")
        print("5. 找到任意请求，在Headers中找到Cookie，复制完整的Cookie值")
        print("6. 将Cookie值粘贴到config.json的cookie字段中")
        return
    
    # 初始化课程对象
    course = BilibiliCourse(auth)
    
    # 获取已购买的课程列表
    print("\n正在获取课程列表...")
    courses = course.get_purchased_courses()
    
    if not courses:
        print("未找到已购买的课程")
        return
    
    # 显示课程列表
    course.list_courses_summary(courses)
    
    # 让用户选择要下载的课程
    print("请选择要下载的课程:")
    print("  输入课程序号下载单个课程 (如: 1)")
    print("  输入 'all' 下载所有课程")
    print("  输入 '1,3,5' 下载多个课程")
    print("  输入 'q' 退出")
    
    choice = input("\n请输入: ").strip()
    
    if choice.lower() == 'q':
        return
    
    # 解析用户选择
    selected_courses = []
    if choice.lower() == 'all':
        selected_courses = courses
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            for idx in indices:
                if 1 <= idx <= len(courses):
                    selected_courses.append(courses[idx - 1])
                else:
                    print(f"警告: 序号 {idx} 超出范围")
        except ValueError:
            print("输入格式错误")
            return
    
    if not selected_courses:
        print("未选择任何课程")
        return
    
    # 初始化下载器
    downloader = BilibiliDownloader(auth.get_session(), auth.download_path)
    courseware_dl = CoursewareDownloader(auth.get_session(), auth.download_path)
    
    # 下载选中的课程
    for idx, course_info in enumerate(selected_courses, 1):
        print(f"\n\n{'#'*60}")
        print(f"开始下载课程 {idx}/{len(selected_courses)}")
        print(f"{'#'*60}")
        
        download_course(course, downloader, courseware_dl, course_info, auth.download_path)
    
    print("\n" + "="*60)
    print("所有课程下载完成!")
    print("="*60)


def download_course(course: BilibiliCourse, downloader: BilibiliDownloader, 
                    courseware_dl: CoursewareDownloader, course_info: dict, base_path: str):
    """
    下载单个课程
    :param course: 课程对象
    :param downloader: 下载器对象
    :param course_info: 课程信息
    :param base_path: 基础路径
    """
    season_id = course_info.get('season_id')
    course_title = course_info.get('title', f'课程_{season_id}')
    
    print(f"\n课程名称: {course_title}")
    print(f"课程ID: {season_id}")
    
    # 获取课程详情
    detail = course.get_course_detail(season_id)
    if not detail:
        print("获取课程详情失败，跳过")
        return
    
    # 创建课程目录
    safe_title = downloader.sanitize_filename(course_title)
    course_path = os.path.join(base_path, safe_title)
    os.makedirs(course_path, exist_ok=True)
    
    # 保存课程信息
    info_file = os.path.join(course_path, "course_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(detail, f, ensure_ascii=False, indent=2)
    
    # 获取所有剧集
    episodes = detail.get('episodes', [])
    print(f"共 {len(episodes)} 个视频")
    
    # 下载课件
    courseware_list = detail.get('courses', [])
    season_id = course_info.get('season_id') or course_info.get('id')
    if courseware_list:
        print(f"\n{'='*60}")
        print(f"发现 {len(courseware_list)} 个课件，开始下载...")
        print(f"{'='*60}")
        courseware_count = courseware_dl.download_courseware(course_path, courseware_list, season_id)
        print(f"\n课件下载完成: {courseware_count}/{len(courseware_list)} 成功")
    else:
        print("\n本课程暂无附赠课件")
    
    # 下载每个剧集
    success_count = 0
    for idx, episode in enumerate(episodes, 1):
        try:
            if downloader.download_episode(episode, course_path, idx):
                success_count += 1
            else:
                print(f"第 {idx} 集下载失败")
        except Exception as e:
            print(f"下载第 {idx} 集时出错: {e}")
    
    print(f"\n课程 '{course_title}' 下载完成: {success_count}/{len(episodes)} 成功")


if __name__ == "__main__":
    main()
