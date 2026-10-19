<p align="center">
  <img src="assets/brand/superjlu-wordmark.png" alt="SuperJLU" width="420">
</p>

<h3 align="center">吉大人的一站式服务</h3>

<p align="center">
  课表、成绩、绩点、学业进度、考试、空教室、校园通知……<br>
  以前要在好几个网站之间来回跳，现在打开一个 App 就够了。
</p>

<p align="center">
  <a href="https://github.com/Runa-Asahi/SuperJLU/releases/latest"><b>⬇️ 立即下载</b></a>
  ·
  <a href="#它能帮你做什么">看看能做什么</a>
  ·
  <a href="#常见问题">常见问题</a>
</p>

---

## 为什么用 SuperJLU？

- **登录一次就够了。** 输入账号密码、收一条微信验证码，之后很长一段时间都不用再登。图形验证码会自动识别，不用你眯着眼睛猜。
- **没网也能看。** 课表、成绩、考试都会存在你自己的手机或电脑上，断网、登录过期的时候照样能查。
- **你的数据只在你手里。** 所有内容都直接和学校服务器通信，账号和登录状态加密保存在本机，不经过任何第三方服务器。
- **手机电脑都能用。** Android 装个 App，Windows 双击就开，界面一样顺手，还有浅色和深色两种主题。

<p align="center">
  <img src="docs/screenshots/grade-analysis-light.jpg" alt="成绩与绩点页面（浅色）" width="48%">
  <img src="docs/screenshots/grade-analysis-dark.jpg" alt="成绩与绩点页面（深色）" width="48%">
</p>
<p align="center"><sub>成绩与绩点页面（截图为示例数据）</sub></p>

## 它能帮你做什么

### 📅 课表：今天上什么课，一眼就知道
按周翻看课表，当天高亮，还会在顶部提醒你下一场考试还有几天。也可以导出到手机日历，课前 15 分钟自动提醒。

### 📊 成绩与绩点：保研、评奖学金前不用再手算
- 一键切换「保研加权」「奖学金加权」「全部课程」等计算方式，加权成绩和绩点马上算好。
- 想按自己学院的规则算？勾选要计入的课程，保存成自己的模板，下次直接用。
- 统计卡片会一直固定在屏幕上，边勾课程边看结果变化。

### 🎓 学业进度：离毕业还差多少学分
按培养方案列出每一类课程（通识、学科基础、专业课……）已修了多少、还差多少，点开就能看到具体是哪几门课，再也不怕漏修。

### 🏫 空教室：找个地方自习
可按日期、按周次，或按自习时间（自动换算节次）查询；选校区、教学楼后马上列出空着的教室。还能按座位数筛选，自动屏蔽实验室这类特殊教室。

### ⏰ 考试安排：倒计时提醒
所有考试的时间地点集中在一页，并显示还剩几天，复习节奏心里有数。

### 📢 通知：重要消息不再错过
把吉大 OA 校内通知和学院官网的通知汇总在一起，可以搜索；订阅「讲座」「补考」「奖学金」这类关键词后，有新通知命中就能看到。

### 🔗 校园网站一键直达
教务系统、学在吉大一键免登录进入；选课、校园卡缴费、图书馆、VPN 也能一键打开，在校外时会自动给出 VPN 地址。

## 三步开始

1. **下载**：到 [Releases 页面](https://github.com/Runa-Asahi/SuperJLU/releases/latest) 下载最新版。
   - **Android 手机**：下载 `SuperJLU-版本号.apk`，直接安装。
   - **Windows 电脑**：下载 `SuperJLU.exe`，双击运行，会自动在浏览器里打开界面，右下角托盘里也能找到它。
2. **登录**：第一次打开会弹出登录框。账号是你的**吉大邮箱前缀**（不是学号），输入密码后，在「智慧吉大」里收微信验证码填进去。
3. **探索**：登录后会自动把课表、成绩、学业等数据同步下来，接下来就随便点点看吧 ✨

> 以后有新版本，直接下载新的安装包覆盖安装即可，数据和登录状态都会保留。

## 微信小程序（实验版）

仓库 [`wechat/`](wechat/README.md) 提供实验版微信原生小程序（手机浏览器辅助同步课表等），运行方式与数据处理见该目录说明。

如需使用或咨询微信小程序，请联系小程序负责人 [@Dramadan-wow](https://github.com/Dramadan-wow)，邮箱 `dramadan070925@qq.com`。**其他 SuperJLU 项目参与者与小程序无关，请勿向其咨询小程序事宜。**

## 常见问题

**登录要用什么账号？**
吉大统一身份认证的账号，也就是你的吉大邮箱 `@` 前面那部分，不是学号。

**会不会泄露我的账号密码？**
不会。SuperJLU 只和学校的服务器直接通信，账号和登录状态加密存在你自己的设备上（Windows 凭据管理器 / Android Keystore），没有任何中间服务器。代码完全开源，欢迎检查。

**在校外能用吗？**
教务仅支持校园网环境内直连。在「更多 → 登录」手动选择「校园网直连」或「校外 WebVPN」后登录；家庭 Wi-Fi、手机流量和热点请使用校外 WebVPN，无需先登录直连教务。程序不自动切换通道，「连接检测」可独立检查 HTTPS 入口。学校 OA 原站可经校园网或学校 VPN 访问；应用内选择「校外 WebVPN」后，OA 通知同步也会走应用内 WebVPN（校外真机验收仍待完成）。学院官网通知和选课入口可独立直接访问。详见 [校外网络说明](docs/offcampus-network.md)。

**数据不是最新的怎么办？**
点右上角的「刷新」按钮，会重新从教务系统同步一次。

**装过旧版「JLU Toolkit」？**
旧版包名不同，请先卸载旧版再安装 SuperJLU。

**怎么确认下载的文件没被篡改？**
每个安装包旁边都有一个 `.sha256` 文件，可以用来核对（Windows 在 PowerShell 里运行 `Get-FileHash 文件名`）。

## 遇到问题或有好点子？

欢迎到 [Issues](https://github.com/Runa-Asahi/SuperJLU/issues) 反馈 bug 或提建议，截图越详细越好。也非常欢迎提交 Pull Request 一起改进 SuperJLU ❤️

## 给开发者和极客

SuperJLU 也能接入 AI 助手（MCP），让 Claude、Cursor 等 AI 助手直接回答「我明天有什么课」「这学期绩点多少」；也可以用命令行查课表、成绩和考试。命令行和 MCP 的安装与使用步骤见 [命令行与开发者文档](docs/cli.md#命令行与-mcp-快速上手)。

本地修改源码后，Windows 可运行仓库内的 `启动SuperJLU.cmd`（需先安装 uv），或在项目目录执行 `uv run --extra captcha python start_local.py`。启动器会运行当前源码、自动打开浏览器，并打印实际地址；8765 已占用时使用其他端口，测试时以本次输出的网址为准。使用期间请保留启动窗口，按 Ctrl+C 停止。

## 特别鸣谢

- **[@Dramadan-wow](https://github.com/Dramadan-wow)**：微信小程序端（[PR #82](https://github.com/Runa-Asahi/SuperJLU/pull/82)）。小程序相关需求请联系 `dramadan070925@qq.com`；其他项目参与者与小程序无关。
- **[@Aohpup](https://github.com/Aohpup)**：成绩加权分析、模板与导入等（[PR #44](https://github.com/Runa-Asahi/SuperJLU/pull/44) / [#45](https://github.com/Runa-Asahi/SuperJLU/pull/45)、[#67](https://github.com/Runa-Asahi/SuperJLU/pull/67)、[#81](https://github.com/Runa-Asahi/SuperJLU/pull/81)）。

欢迎关注他们的 GitHub ⭐

---

<p align="center"><sub>SuperJLU 是同学自发开发的开源项目，与吉林大学官方无关。</sub></p>
