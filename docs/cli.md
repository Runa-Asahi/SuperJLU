# SuperJLU 命令行与开发者文档

> 普通同学直接下载 App 就行，不需要看这里。本页面向想用命令行、MCP 或参与开发的同学。

## 安装命令行版

```bash
# 推荐装在独立环境里（uv 或 pipx 二选一）
uv tool install "jlu-toolkit[captcha] @ git+https://github.com/Runa-Asahi/SuperJLU"
pipx install "jlu-toolkit[captcha] @ git+https://github.com/Runa-Asahi/SuperJLU"
# 需要 MCP 时把 [captcha] 换成 [captcha,mcp]

jlu-toolkit ui --open        # 打开网页界面
```

升级：`uv tool upgrade jlu-toolkit` / `pipx upgrade jlu-toolkit`。查看版本：`jlu-toolkit --version`。

> 原名 JLU Toolkit。为兼容，Python 包名仍为 `jlu_toolkit`，命令行仍是 `jlu-toolkit`（等价别名 `superjlu`），配置目录不变。


#### 培养方案课程明细（0.3.13）

```bash
jlu-toolkit plan --probe      # 只读：应用/模块/动作、字段名+标题、行数（无数值）
jlu-toolkit plan --refresh    # 拉取到 data/plan_courses.json（sync 也会做）
jlu-toolkit plan --status 未修 --nature 必修
```
网页「学业」页各课组可展开查看课程（已修/在修/未修），可按学期、性质筛选。MCP 工具：`plan_courses`。

#### 空教室筛选（0.3.11）

```bash
jlu-toolkit rooms --list-campuses | --list-buildings --campus 01 | --list-types | --list-fields
# 按日期：校区 + 教学楼 + 类型 + 节次 + 座位数范围
jlu-toolkit rooms --campus 01 --building XXX --type XX --date 2026-10-20 --periods 3-4 --seats 100- --exam-seats 50-120 --sort -seats
# 按周次：第 6-8 周 周三
jlu-toolkit rooms --campus 01 --weeks 6-8 --weekday 3 --periods 1-2
# 元数据里的其它检索字段（「更多条件」）
jlu-toolkit rooms --campus 01 --field 字段名=值
```
结果自动翻页取全；网页「教室」页支持两种模式、校区→教学楼联动、范围筛选、点表头排序。

## 快速开始
```bash
jlu-toolkit ics examples/schedule.csv --first-monday 2026-09-07 -o 课表.ics
jlu-toolkit gpa examples/grades.csv --term 2025-2026-1   # 简单学分加权，见下方「绩点说明」
jlu-toolkit today examples/schedule.csv --week 3 --weekday 1
```
省略 CSV 路径时，`ics` / `today` 读 App 的数据目录，和 App 看到的是同一份课表（教务课表 + 调课/停课〔按 App 设置〕+ 自己的修改）；`fetch` 导出的 `schedule.csv` 也是这一份。MCP 的 `courses_on_day` 同理。
CSV 格式参考 `examples/`。周次支持 `1-16`、`1-15单`、`2-16双`、`1,3,5`。

## 从教务系统自动拉取（含二次认证）

本科教务：`https://iedu.jlu.edu.cn`（金智 jwapp）  
统一身份认证：`https://cas.jlu.edu.cn/tpass/login`

**账号是邮箱前缀，不是学号。**

登录流程：
1. 提交邮箱前缀 + 密码（密码经页面同款 3DES：`rsa = strEnc(账号+密码+lt,"1","2","3")`）
2. 若出现「二次认证」：下载图形验证码 → 输入后调用发送接口 → 在「智慧吉大」收取微信验证码 → 提交完成登录
3. 会话 cookie 登录成功后自动保存，下次未过期可免登录（存储方式见下）

### 凭据与会话的存储（加密）

- 有系统钥匙串时（Windows 凭据管理器 / macOS 钥匙串 / Linux Secret Service）：随机生成的密钥存进钥匙串，
  会话和（可选保存的）密码用 AES-256-GCM 加密后写到 `~/.config/jlu-toolkit/session.enc`、`credentials.enc`。
- 钥匙串不可用时（Termux、无桌面的服务器）：退回明文 `session.json` / `credentials.json`，权限 600，并在终端给出警告。
  这种情况下**不建议** `--save-credentials`。设环境变量 `JLU_TOOLKIT_NO_KEYRING=1` 可强制用文件。
- 旧版本留下的明文文件会在第一次读取时自动转成加密文件并删除明文。
- 数据只存在你自己的电脑上，不会上传到任何服务器。

### 会话过期

智慧吉大的微信验证码无法也不应绕过，会话过期后需要你重新登录一次：

```bash
jlu-toolkit status           # 查看会话状态（不联网）；需要登录时退出码为 3
jlu-toolkit status --check   # 访问教务一次，确认会话是否仍有效
jlu-toolkit fetch --force-login
```

请求被教务重定向到登录页时，CLI 会提示「登录会话已过期，请重新登录」；MCP 有 `session_status` 工具；
本地网页可读 `GET /api/session`（见下方「本地 API」）。本工具不会在后台定时访问教务来"保活"。

### 网络说明

| 地址 | 说明 |
|------|------|
| `cas.jlu.edu.cn` | 公网可访问（登录、验证码、发微信码） |
| `iedu.jlu.edu.cn` | 教务业务站；部分网络需**校园网或学校 VPN** |

```bash
jlu-toolkit fetch --probe
```

### 拉取课表和成绩
```bash
# 交互：密码 →（如需）图形验证码路径提示 → 微信验证码
jlu-toolkit fetch --user 你的邮箱前缀

# 可选：保存账号密码；会话会在登录成功后自动保存
jlu-toolkit fetch --user 你的邮箱前缀 --save-credentials

# 强制重登（忽略已保存会话）
jlu-toolkit fetch --user 你的邮箱前缀 --force-login
# 登录成功后会自动打开课表/成绩应用入口（避免接口 403）
# 若仍 403：加 --debug 查看是否有 CASTGC / _WEU

# 只拉课表 / 成绩 / 考试 / 指定学期
jlu-toolkit fetch --user 你的邮箱前缀 --what schedule --term 2025-2026-2
jlu-toolkit fetch --what exams          # 考试安排 → exams.csv，并打印倒计时
jlu-toolkit exams exams.csv             # 离线查看考试倒计时
```

图形验证码图片：
- **Termux**：优先保存到 `~/storage/downloads/jlu_cas_captcha.jpg`（请先 `termux-setup-storage`）
- 其他环境：当前目录下的 `jlu_cas_captcha.jpg`

> MCP **不会**代你登录教务；请先用上面的命令导出 CSV，再把路径配给 MCP。

### Termux（Android）示例
```bash
pkg install python git python-pillow python-cryptography   # cryptography 用 pkg 的预编译包，免去在手机上编译
termux-setup-storage
pip install -U "jlu-toolkit[captcha] @ git+https://github.com/Runa-Asahi/SuperJLU"
# Termux 没有系统钥匙串：会话以 600 权限明文保存在 ~/.config/jlu-toolkit/，首次会打印一条警告，属正常
jlu-toolkit fetch --probe
jlu-toolkit fetch --user 你的邮箱前缀 --force-login
# 登录成功后会自动打开课表/成绩应用入口（避免接口 403）
# 若仍 403：加 --debug 查看是否有 CASTGC / _WEU
jlu-toolkit explore            # 只读探测，报告在 ~/storage/downloads/
jlu-toolkit ui                 # 手机浏览器打开 http://127.0.0.1:8765/
# 图形验证码默认自动识别（纯 Pillow，无需 ddddocr）
# 识别错了会自动刷新最多 5 次，再不行才让你手输
# 需要看图时加：--show-captcha
```

## 网页界面（`jlu-toolkit ui`）

```bash
jlu-toolkit ui            # 浏览器打开 http://127.0.0.1:8765/
jlu-toolkit ui --demo     # 用示例数据先看看效果
```

成绩页支持加权成绩、加权绩点，以及保研加权（不含限选课程）、奖学金加权、所有课程三个内置模板。模板规则参考 [JLU-score-calculator](https://github.com/Aohpup/JLU-score-calculator)，仅作起点；不同学院政策不同，请核对当年规定，逐门调整后另存为自定义模板。模板保留基础规则与手动覆盖，新增课程按基础规则选择；原有方案仍可使用。

可导入或拖入 Excel / CSV 成绩单（最多 25 MB，支持中英文表头、标题行、多工作表、UTF-8 / GB18030 CSV）。成绩页默认读取当前登录账号的教务成绩，并在已登录时自动同步。文件导入收在“其他方式 · 文件导入（可选）”中；导入数据单独保存在当前数据目录的 `imported_grades.json`，不覆盖教务成绩，可随时点击“返回教务成绩”。重新打开页面或登录后回到教务成绩，已导入文件仍可从可选入口重新查看。`--demo` 使用临时目录，正式启动使用本机数据目录。

搜索、学期与性质多选、成绩 / 绩点 / 学分范围、计入状态和成绩状态只改变显示；加权结果始终统计所有已计入课程。批量计入 / 排除只作用于筛选结果，点击列标题可排序。不及格课程整行标红。教务课程优先使用提供的单科绩点，缺失时标明“估算”；导入成绩单缺少绩点时显示“—”。原教务的“通过”类课程不参与加权。

成绩页右上角“？”提供规则、学院官网与政策查询关键词；首次打开成绩页会提醒核对政策。所有导入、模板和计算都在本机进行。

- **课表**：周视图，左右滑动或按钮切换周次，今日高亮；首页顶部显示下一场考试倒计时
- **成绩**：顶部显示教务官方「学分绩点统计」（只读）；下方每门课一个勾选框，实时计算所选课程的绩点；可把勾选结果另存为命名方案（如「保研」「综测」）
- **考试**：倒计时列表（3 天内标红）
- **学业**：培养方案总学分进度、各类课程（课组）要求/已获/还差学分，未完成的排在前面
- **设置**：开学日期自动取自教务校历（可手动覆盖）、导出 iCal（使用教务节次时间）
- 右上角「刷新」（等同 `jlu-toolkit sync`）使用终端登录时保存的会话从教务重新拉取，不会弹出登录；会话失效时在终端执行 `jlu-toolkit fetch --force-login`

仅监听 `127.0.0.1`，页面无任何 CDN/外部资源，数据保存在 `~/.config/jlu-toolkit/data/`。

### 一键同步（非交互）

```bash
jlu-toolkit sync    # 课表/成绩/考试/校历/节次时间/官方绩点/学业完成 → ~/.config/jlu-toolkit/data/
```
终端只打印条数、成功/失败等摘要，**不打印绩点、学分等个人数值**；任何一项失败时退出码为 2。

## 空教室（`jlu-toolkit rooms`）

教务的「空闲教室查询」必须带**校区、空闲日期、空闲节次**，不带会直接返回错误。

```bash
jlu-toolkit rooms --list-campuses                     # 校区代码
jlu-toolkit rooms --list-buildings --campus 校区代码    # 教学楼代码（可选）
jlu-toolkit rooms --campus 校区代码 --date 2026-10-16 --periods 3-4
jlu-toolkit rooms --probe                             # 只读探测接口/参数组合，只打印结构
```

- 应用名是 `kxjas`（页面 `/jwapp/sys/kxjas/*default/index.do#/kxjscx`，`kxjscx` 只是前端路由）。先进入 `kxjas` 入口（EMAP 需要先换取 `_WEU`），再抓取页面脚本找出 `*.do` 接口，再读取模块元数据（动作 URL、查询字段、校区/教学楼字典），按元数据推断参数，并尝试几种常见的金智参数格式
- 第一次查询成功后，接口和参数格式会保存到 `rooms_profile.json`，以后直接复用
- 周次、星期按教务校历自动推算
- 网页「教室」页和 MCP 工具 `free_rooms` / `list_campuses` 用的是同一套逻辑

## 官方绩点探测（`jlu-toolkit gpa --probe`）

```bash
jlu-toolkit gpa --probe
```

进入成绩应用 `cjcx`，扫描页面脚本与模块元数据，列出全部动作与字段名；对名称含绩点/学分统计特征的动作试调用，报告只含结构（状态码、字段名、匹配到的官方字段标签），不含绩点数值。

## 绩点说明

`jlu-toolkit gpa`、`fetch` 输出的绩点目前是**全部课程的简单学分加权平均**：百分制 60 分记 1.0、每多 1 分 +0.1、90 分及以上 4.0；等级制按 优秀95/良好85/中等75/及格65 换算；「通过」类不计入。

网页「成绩」页顶部预留了教务**官方**统计。吉大目前没有「学分绩点统计」接口：若成绩接口返回了单科绩点，就显示按教务单科绩点算出的学分加权；否则显示「暂不可用」。各课组的已获学分在教务未提供时，按「培养方案课程 → 课组」映射加上已通过成绩推算，页面上标注「按成绩推算」。

自算绩点**不等于**教务或学院的官方口径（保研、综测等会剔除体育、公选、重修等不同课程）。请在网页界面里勾选需要计入的课程，并保存为自己的方案。

## 探测更多教务功能（`jlu-toolkit explore`）

```bash
jlu-toolkit explore
```

v2 会额外用内存中的学号/方案代码探测官方绩点与课组明细（不写入报告），并从空教室应用前端代码中提取接口路径（`discover`）。

用已保存会话**只读**探测考试安排、空教室、培养方案/学业完成、学期校历、个人信息等候选接口，生成 `jlu_explore_report.json`（Termux 下在「下载」目录）。
报告**只含状态码、JSON 键名、行数、字段名，不含任何值**（不含姓名、学号、成绩），可以直接贴给开发者用于适配。
绝不调用选课、退课、报名、评教提交等写接口。

## 接入 AI 助手（MCP）

MCP 依赖需要 Python 3.10 或更高版本；普通 CLI / Web UI 仍支持 Python 3.9。Python 3.9 安装时会跳过不兼容的可选 MCP 依赖，以免影响基础功能和 `uv` 的跨版本依赖解析。
```bash
pip install "jlu-toolkit[mcp] @ git+https://github.com/Runa-Asahi/SuperJLU"
```
```json
{"mcpServers": {"jlu": {"command": "jlu-toolkit-mcp",
  "env": {"JLU_SCHEDULE_CSV": "/path/课表.csv", "JLU_GRADES_CSV": "/path/成绩.csv"}}}}
```

## 路线图
- [x] 课表/成绩文件导入、绩点计算、iCal 导出、MCP 接口
- [x] 教务 HTTP 自动导出（CAS 3DES + 二次认证 + 验证码自动识别；会话本地复用）
- [x] 本地网页界面：课表周视图、成绩勾选、命名绩点方案、考试倒计时、iCal 导出
- [x] 考试安排拉取与倒计时（接口按金智通用 `studentWdksapApp` 实现，待吉大实测确认）
- [x] `explore` 只读探测 + 脱敏报告
- [x] 教务校历自动识别开学日期/当前周、真实节次时间、官方学分绩点、学业完成（课组）进度
- [~] 空教室：已实现 `jlu-toolkit rooms`、网页「教室」页和 MCP `free_rooms`；吉大的接口名/参数正通过 `rooms --probe` 实测确认
- [~] 官方绩点：用与空教室相同的 EMAP 页面发现扫描 `cjcx` 应用，找含 jd/xfjd 等的动作；`jlu-toolkit gpa --probe` 输出动作/字段名。找到后 source=`official`，否则仍回退到教务单科绩点加权
- [ ] 官方绩点口径（保研/综测）预设方案、不同学院规则可配置
- [ ] MCP 接入考试与绩点方案；桌面托盘挂件

欢迎 PR 和 ⭐！

## 本地 API：会话状态

`GET /api/session`（新增，只读本地记录，不访问教务）：

```json
{"state": "ok|expired|missing|unknown", "logged_in": true, "needs_login": false, "session_expired": false,
 "message": "已登录", "checked_at": 1760000000, "saved_at": 1760000000, "storage": "keyring:WinVaultKeyring"}
```

`POST /api/*` 遇到会话过期时返回 HTTP 401 和 `{"ok": false, "error": "...请重新登录...", "session_expired": true}`；
其它接口的返回结构不变。

## Android

Android 版（`android/`，Chaquopy + WebView）的构建与签名发布约定见 [docs/android-release.md](android-release.md)。
Android 下凭据用 Android Keystore 包裹的主密钥加密（`backend_name()` = `android-keystore`），需要 Chaquopy 提供的 `cryptography==42.0.8`。

## OA 校内通知（只读，实验性）

吉大 OA（`oa.jlu.edu.cn`，万户 ezOFFICE）仅校园网/VPN 可达。本工具只发 GET，绝不做审批/表单操作。

```
jlu-toolkit oa --probe                 # ASCII 计数：登录页字段名、匿名/会话访问、行数、分页、栏目数、详情结构
jlu-toolkit oa notices --category 179577 --keyword 放假 --limit 20 [--json]
```

- 列表：`PortalInformation!jldxList.action?channelId=<栏目>&startPage=<页>`（179577 = 校内通知）
- 详情：`PortalInformation!getInformation.action?id=<id>&channelId=<栏目>`
- 存储：`data/oa_notices.json` → `{updated, channels:{id:name}, channels_items:{id:[item]}}`
- 关键字：默认用服务端搜索 `GET jldxList.action?searchId=<UTF-8 关键字>`（**不带 channelId**；PC 实测带 channelId 会忽略关键字，GBK 中文返回 0）。服务端检索跨全部栏目且可能命中正文，所以结果标题不一定含关键字。指定 `--category` 时按条目链接中的 channelId 本地筛选（`channel_filtered: true`），可能因此变少；不指定时结果可能来自任意栏目。`search` 字段为 `server`；若服务端搜索不可用（`oa._search_pref = ()`）则退回本地跨页过滤标题/单位（`search: local`）。
- `oa --probe` 的 `search_variants`：每个变体给出 ascii/cjk/罕见词 `zzqx9` 的行数、与未过滤第 1 页的 id 重叠数、标题命中数；`filters` 判定 = 罕见词 0 行 且 ascii 命中率 ≥ 80% 且 ascii 重叠 < 行数。
- MCP：`oa_notices(category, keyword, limit, refresh)`

### 拟议 /api 形状（供 Web UI，后端尚未实现）

`GET /api/oa/notices?category=&keyword=&limit=` →

```json
{"ok": true, "channel": "179577", "channel_name": "校内通知", "count": 2, "fetched_at": "2026-10-15T09:00:00",
 "items": [{"id": "123", "title": "...", "time": "2026-10-01 08:05", "dept": "...", "top": true, "url": "https://oa.jlu.edu.cn/..."}]}
```

`GET /api/oa/channels` → `{"channels": [{"id": "179577", "name": "校内通知"}]}`；出错 `{"ok": false, "error": "...", "login_needed": true}`。

## 校园站点会话（sessions）

`jlu_toolkit/sessions.py` 统一管理各站点登录会话（只读本地，不后台轮询，不绕过验证码）。

| id | 站点 | host | 认证 |
|---|---|---|---|
| jwxt | 教务系统 | iedu.jlu.edu.cn | CAS（沿用原有 session.enc） |
| pay | 校园缴费 | ip.jlu.edu.cn | 自有（卡号+密码+验证码），只读 |
| xsxk | 选课系统 | icourses.jlu.edu.cn | 自有（AES 密码+验证码，token 头） |
| ilearn | 学在吉大 | ilearntec.jlu.edu.cn | 自有（邮箱+密码+验证码；课程中心或经 CAS，待确认） |
| vpn | WebVPN | vpn.jlu.edu.cn | CAS |
| lib | 图书馆 | lib.jlu.edu.cn | 首页无需登录；个人中心 CAS（optional_login） |

> 探测备注（`campus --probe`，2026-10）：`pay` / `xsxk` 实际是自有表单+验证码（非 CAS）；
> `ilearn` 课程中心会经 `ilearn.jlu.edu.cn/cas-server` 桥到 `cas.jlu.edu.cn`；
> `lib` 门户匿名，个人中心走 CAS `service=.../sso/login/3rd/30569`。上表认证列待 sessions 注册表后续对齐。

**策略**：cookie 一律经 `secure_store` 加密保存为 `session-<id>.enc`；状态文件 `sessions_status.json` 只记 `state/checked_at/reason`；
从不保存任何支付信息，缴费站只读；带验证码的站点不保存密码（除非用户明确选择保存）；教务凭据行为不变。

```
jlu-toolkit sessions [--json]          # 各站状态
jlu-toolkit sessions check <id>        # 用户触发：跑一次存活检查（有钩子时）
jlu-toolkit sessions clear <id>
```

- HTTP：`GET /api/sessions` → `{"ok":true,"sites":[{"id","name","host","auth","vpn","captcha","optional_login","state","checked_at","needs_login","message","has_check"}]}`，
  `state` ∈ ok/expired/missing/unknown。任何 `POST /api/*` 遇到某站会话过期返回 401：`{"ok":false,"error":"...","session_expired":true,"site":"<id>"}`（教务为 `"jwxt"`）。
- MCP：`sessions_status()`，返回同上。
- 钩子：`jlu_toolkit/campus.py`（`feat/campus-probe`）提供 `check_<id>(session) -> {"logged_in": True/False/None, "reason": str}`
  （session 是带该站 cookie 的 `JwxtClient`，只发一次无副作用 GET；判定过期时先 `mark_expired` 再抛 `SiteSessionExpired`；
  None → unknown）与 `vpn_url(url)`（AES-128-CFB / key=`Didida1127Didida` → `https://vpn.jlu.edu.cn/{scheme}/{token}{path}`）；
  也可 `sessions.register_check(id, fn)` / `sessions.register_vpn_url(fn)`。无 campus 且未注册时 `vpn_url` 抛 `NotImplementedError`。
- 探测：`jlu-toolkit campus --probe [--json]`（只读，无个人数值）。
- 站点代码抛 `sessions.SiteSessionExpired("<id>")`，并可调用 `sessions.mark_expired(id, reason)`。

## 登录保持与离线缓存

统一认证要微信验证码，所以**不做**用密码静默重登。改为：

- **CAS 单点登录持久化**：每次 `save_session()` 后，把 `cas.jlu.edu.cn` 主机上的全部 cookie（含 TGC 类长期票据，不假设具体名字）加密保存为站点 `cas`。
  登录表单若有 `remember*` / `rememberMe` 字段会自动开启。
- **静默换票** `sessions.refresh_via_cas(site)`：仅 `auth == "cas"` 且已知 service 的站点（目前只有 `jwxt`）。
  教务会话过期时（`session_alive` / 接口请求落到登录页）自动尝试一次：带 CAS cookie 访问 `tpass/login?service=…`，回到教务则保存新会话；
  落在 CAS 登录页则把 `cas` 标记为过期，照常抛 `SessionExpiredError`（界面显示应用内登录）。
- **保活** `sessions.keepalive()`：一次轻量 GET。`jlu-toolkit sessions keepalive [--json]`（失效退出码 3）；
  `POST /api/session/keepalive`（App 前台约每 15 分钟调用；Python 端没有后台循环）。
- **加密数据缓存**：`secure_store.save_json(path, obj)` / `load_json(path, default)` / `json_exists(path)`。
  `official_gpa.json`、`completion.json`、`plan_courses.json` 改为加密 `.enc`（旧明文首次读取时迁移）；
  每次写入在 `data/cache_meta.json` 记 `updated_at`。课表/成绩/考试 CSV 与设置、OA 缓存暂保持原格式。
- **离线标记**：`GET /api/session`、`GET /api/data` 增加 `offline`（教务会话不是 ok 但本地有缓存）与 `cached_at`（ISO 时间）。
### OA 关键词订阅与提醒（增量同步）

只请求列表**第 1 页**（含置顶），按公告 id 与本地已见记录去重；绝不全量翻页，栏目之间间隔 2 秒。首次运行只记录现有 id，不发提醒。

```
jlu-toolkit oa subscribe add -k 讲座,奖学金 [--dept 教务处] [--category 179577]
jlu-toolkit oa subscribe list [--json]
jlu-toolkit oa subscribe remove <id>
jlu-toolkit oa watch [--interval 30] [--once]     # 间隔最小 10 分钟
```

- 匹配：关键词出现在标题或发文单位中；设置了 `--dept` 时单位须包含其一。
- 提醒：plyer（`pip install jlu-toolkit[notify]`）→ Termux `termux-notification` → Windows PowerShell 通知 → Linux `notify-send` → 仅打印；任何失败都不会中断。
- 存储（`config_dir()/data`）：`oa_seen.json`、`oa_subscriptions.json` `{rules:[{id,keywords,depts,channel,created}]}`、`oa_matches.json` `{matches:[{rule_id,keywords_hit,notice,matched_at}]}`（最多 300 条）。
- MCP：`oa_new_matches(limit=20, since="")` → `{rules, matches}`（只读本地）。

Web API（仅 127.0.0.1）：

| 方法 | 路径 | 请求 | 返回 |
|---|---|---|---|
| GET | `/api/oa/subscriptions?limit=20` | – | `200 {"ok":true,"rules":[...],"matches":[...]}` |
| POST | `/api/oa/subscriptions` | `Content-Type: application/json`，`{"keywords":["讲座"] 或 "讲座,补考","depts":[...]（可选）,"channel":"179577"（可选）}` | `201 {"ok":true,"rule":{id,keywords,depts,channel,created}}`；校验失败 `400 {"ok":false,"error":"..."}` |
| DELETE | `/api/oa/subscriptions/<id>` 或 `?id=<id>` | – | `200 {"ok":true,"removed":"<id>"}`；不存在 `404`；缺 id `405` |

校验：至少 1 个关键词，每个 ≤40 字、最多 20 个（自动去重、去空白，支持中文逗号）；channel 必须是数字；规则最多 100 条。

## Windows 一键版 SuperJLU.exe（PyInstaller，测试中）

双击 `SuperJLU.exe`（单文件、无控制台窗口）：在 127.0.0.1:8765（被占用时改用空闲端口）后台启动界面并打开浏览器，系统托盘显示 SuperJLU 图标，菜单「打开 SuperJLU」「退出」。
再次双击时，如果已有实例在运行，只会打开浏览器。日志：`%USERPROFILE%\.config\jlu-toolkit\desktop.log`。

- 入口：`jlu_toolkit/desktop.py`（`python -m jlu_toolkit.desktop` 在 Linux/macOS 也能用；没有 pystray 时不显示托盘）
- 构建：`pip install ".[desktop,captcha]" pyinstaller && python packaging/build_windows.py` → `dist/SuperJLU.exe`
- 图标：`assets/brand/superjlu.ico`（exe 图标和托盘图标都用它）
- CI：`.github/workflows/build-windows.yml`，只在手动运行或推 `v*` 标签时构建，产物 `SuperJLU-windows`
