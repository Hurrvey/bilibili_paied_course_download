# B站课程批量下载工具

这是一个用于批量下载B站已购课程的Python工具，支持视频和课件下载。

## 功能特点

- ✅ 自动获取已购买的所有课程列表
- ✅ 支持选择下载单个或多个课程
- ✅ 自动按课程名称创建目录结构
- ✅ 支持DASH格式视频下载（自动选择最高可用画质）
- ✅ 自动合并视频和音频流
- ✅ **支持课件下载**（PDF/文档自动下载，网盘链接自动保存）
- ✅ 显示下载进度
- ✅ 自动跳过已下载的文件
- ✅ **浏览器自动化获取Cookie**（可选）

## 安装依赖

```bash
pip install -r requirements.txt
```

**重要**: 必须安装 [ffmpeg](https://ffmpeg.org/download.html) 并添加到系统PATH，用于合并视频和音频流。

## 配方法一：自动获取Cookie（推荐⭐）

最简单的方式，运行自动化工具：

```bash
python browser_helper.py
```

程序会：
1. 自动打开Chrome浏览器
2. 访问B站课程页面
3. 等待你登录（可以扫码或账号密码登录）
4. 自动捕获Cookie并保存到`config.json`

完成后即可直接运行 `python main.py` 开始下载！

---

### 方法二：手动获取Cookie

#### 1. 创建配置文件

复制 `config.json.example` 为 `config.json`:

```bash
copy config.json.example config.json
```

#### 2. 获取Cookie

**方式A：使用Console（最简单）**

1. 在浏览器中登录 [B站课程页面](https://www.bilibili.com/cheese/mine/list)
2. 按 `F12` 打开开发者工具
3. 切换到 `Console`（控制台）标签
4. 输入以下代码并回车：
   ```javascript
   document.cookie
   ```
5. 复制输出的完整Cookie字符串

**方式B：从Network标签获取**

1. 在浏览器中登录 [B站课程页面](https://www.bilibili.com/cheese/mine/list)
2. 按 `F12` 打开开发者工具
3. 切换到 `Network`（网络）标签
4. 刷新页面
5. 在左侧找到以 `list` 或 `api.bilibili.com` 开头的请求
6. 点击该请求，在右侧找到 `Headers` → `Request Headers` → `Cookie`
7. 复制完整的Cookie值

详细教程参见：[获取Cookie教程.md](获取Cookie教程.md)

**⚠️ 注意事项：**
- Cookie必须在登录后的课程页面获取
- 确保Cookie包含 `SESSDATA`、`bili_jct`、`buvid3` 等关键字段
- Cookie会过期，如果下载失败请重新获取

#- Cookie会过期，如果下载失败请重新获取

### 3. 编辑配置文件

打开 `config.json`，填入Cookie信息：

**方式一**（推荐）：
```json
{
  "cookie": "你复制的完整Cookie字符串",
  "download_path": "./downloads"
}
```

**方式二**：
```json（包括视频和课件）
{
  "cookie": "",
  "download_path": "./downloads"
}
```

## 使用方法

运行主程序：

```bash
python main.py
```
课件/
│   │   ├── 2026操作系统.pdf (直接下载的课件)
│   │   └── 某课件_网盘链接.txt (网盘类课件的链接和提取码)
│   ├── 01. 第一课.mp4
│   ├── 02. 第二课.mp4
│   └── ...
├── 课程2/
│   ├── course_info.json
│   ├── 课件/
│   │   └── ...
│   ├── 01. 开篇.mp4
│   └── ...
└── ...
```

## 课件下载说明

程序支持两种类型的课件：

### 1. 直接下载类型
- **PDF、DOC、ZIP等文件**：自动下载到`课件`目录
- 显示下载进度。推荐使用 `python browser_helper.py` 自动获取，或按照手动方法重新获取并更新config.json文件

### Q: 提示"未找到ffmpeg"或下载失败
A: 请安装ffmpeg并确保已添加到系统PATH环境变量中。Windows用户可以从 https://ffmpeg.org/download.html 下载，解压后将bin目录添加到PATH

### Q: 课件下载失败怎么办？
A: 
- 对于直接下载的PDF等文件，检查网络连接和磁盘空间
- 对于网盘链接，程序会自动保存链接和提取码到txt文件，请手动下载
- 部分课件可能需要在浏览器中手动下载

### Q: 如何更新Cookie？
A: 运行 `python browser_helper.py` 会自动更新，或手动修改config.json中的cookie字段

### Q: 下载速度很慢
A: 这取决于你的网络状况和B站服务器速度

### Q: 可以下载未购买的课程吗？
A: 不可以，只能下载已购买的课程

### Q: Chrome浏览器自动化失败
A: 确保已安装Chrome浏览器，程序会自动下载对应版本的ChromeDriver课程
- 输入 `1,3,5` - 下载第1、3、5个课程
- 输入 `q` - 退出程序

## 目录结构

下载后的文件结构如下：

```
downloads/
├── 课程1/
│   ├── course_info.json (课程详细信息)
│   ├── 01. 第一课.mp4
│   ├── 02. 第二课.mp4
│   └── ...
├── 课程2/
│   ├── course_info.json
│   ├── 01. 开篇.mp4
│   └── ...
└── ...
```

## 注意事项

1. **Cookie有效期**: Cookie可能会过期，如果下载失败请重新获取Cookie
2. **网络稳定性**: 建议在网络稳定的环境下使用
3. **存储空间**: 确保有足够的磁盘空间存储视频文件
4. **合法使用**: 仅下载自己购买的课程，仅供个人学习使用
5. **ffmpeg**: 必须安装ffmpeg才能正常下载，未安装时下载会失败

## 常见问题

### Q: 提示"未登录或cookie已失效"
A: 重新获取Cookie并更新config.json文件

### Q: 提示"未找到ffmpeg"或下载失败
A: 请安装ffmpeg并确保已添加到系统PATH环境变量中。Windows用户可以从 https://ffmpeg.org/download.html 下载，解压后将bin目录添加到PATH

### Q: 下载速度很慢
A: 这取决于你的网络状况和B站服务器速度

### Q: 可以下载未购买的课程吗？
A: 不可以，只能下载已购买的课程

## 免责声明

本工具仅供学习交流使用，请勿用于商业用途。下载的视频内容版权归B站和课程作者所有，请遵守相关法律法规。

## 许可证

MIT License