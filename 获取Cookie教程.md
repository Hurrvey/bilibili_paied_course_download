# B站课程Cookie获取详细教程

## 为什么需要Cookie？

Cookie是你的登录凭证，程序需要它来验证你的身份并获取你购买的课程列表。

## 获取步骤

### 方法一：自动获取（强烈推荐⭐）

**最简单、最快速的方法！**

1. **运行自动化工具**
   ```bash
   python browser_helper.py
   ```

2. **等待浏览器打开**
   - 程序会自动打开Chrome浏览器
   - 自动访问B站课程页面

3. **手动登录B站**
   - 在打开的浏览器中登录你的B站账号
   - 可以扫码登录或账号密码登录

4. **等待30秒**
   - 登录完成后，保持浏览器打开
   - 程序会自动倒计时30秒
   - 期间会自动捕获Cookie和API请求

5. **完成！**
   - 程序会自动关闭浏览器
   - Cookie已保存到 `config.json`
   - 可以直接运行 `python main.py` 开始下载

**优点：**
- ✅ 无需手动操作复杂步骤
- ✅ 自动保存到配置文件
- ✅ 同时验证API可用性
- ✅ 出错率极低

---

### 方法二：使用Console获取（手动方式）

1. **打开B站课程页面**
   - 在浏览器中访问：https://www.bilibili.com/cheese/mine/list
   - 确保你已经登录

2. **打开开发者工具**
   - 按键盘 `F12` 键
   - 或者右键点击页面 → 选择"检查"

3. **切换到Console标签**
   - 在开发者工具顶部找到 `Console`（控制台）标签
   - 点击切换到该标签

4. **获取Cookie**
   - 在下方列表中点击第一个
   - 在右侧面板中找到Cookie部分
   - 这里会显示一长串文本，这就是你的Cookie

5. **复制Cookie**
   - 右键点击显示的Cookie文本
   - 选择"Copy string contents"（复制字符串内容）
   - Cookie已复制到剪贴板

## Cookie示例

正确的Cookie应该类似这样（这只是示例，请使用你自己的）：

```
_uuid=12345678-1234-1234-1234-123456789ABC; buvid3=12345678-1234-1234-1234-123456789ABC; SESSDATA=abcdef123456; bili_jct=xyz789; ...
```

## 配置Cookie

将复制的Cookie粘贴到 `config.json` 文件中：

```json
{
  "cookie": "这里粘贴你复制的完整Cookie",
  "download_path": "./downloads"
}
```

## 常见问题

### Q: 推荐使用哪种方法？
A: **强烈推荐方法一（自动获取）**，只需运行 `python browser_helper.py` 然后登录B站即可，完全自动化

### Q: 自动获取失败怎么办？
A: 确保已安装Chrome浏览器，如果还是失败，可以使用方法二或方法三手动获取

### Q: 提示"未登录或cookie已失效"怎么办？
A: Cookie有时效性，请重新获取最新的Cookie

### Q: 找不到Console标签？
A: 确保你按的是F12而不是其他键，如果还是找不到，试试按 `Ctrl+Shift+J`（Windows）直接打开Console

### Q: 获取的Cookie能用多久？
A: 一般可以使用几天到几周，失效后重新获取即可

### Q: Cookie安全吗？
A: Cookie是你的登录凭证，不要分享给他人，仅在本地config.json中使用

## 获取成功标志

运行 `python main.py` 后，如果看到：
```
登录成功! 用户名: 你的用户名
```
说明Cookie配置正确！
