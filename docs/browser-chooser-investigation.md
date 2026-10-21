# Android 网页选择与应用内默认

## 解决的问题

在 OPPO Find X8 Ultra / ColorOS 16 / Android 16 上，直接包装网页 URL 的系统选择器曾只列出官方浏览器，且可能跳过面板。当前实现先查询能处理网络网页的应用，再把显式组件和原网址交给系统面板；「更多」提供独立的应用内默认设置。

历史失败记录和后续设备检查见 [浏览器选择 TODO](TODO-browser-selection.md)。

## 候选发现

- Manifest 只声明 HTTP / HTTPS 的 ACTION_VIEW + BROWSABLE，分别覆盖无 MIME、`text/html` 和 `application/xhtml+xml`，共六种 `<queries>` 签名。
- 对当前网址分别查询三种 MIME 组合，使用 `MATCH_ALL | MATCH_DEFAULT_ONLY | GET_RESOLVED_FILTER`。`MATCH_DEFAULT_ONLY` 要求接收器声明 DEFAULT 类别，不代表仅返回默认浏览器；`MATCH_ALL` 不能绕过应用可见性或厂商限制。
- 读取公开的匹配 IntentFilter，检查通用网络 scheme、VIEW、BROWSABLE，排除带域名／路径限制的深链接、本地文件接收器、停用／暂停、未导出或缺少启动权限的组件。
- 按包去重，优先使用无 MIME 的网页入口。匹配 HTML / XHTML 的入口保留其 MIME；通过 `setDataAndType` 同时保留原网址，避免单独设置 type 时丢失地址。
- 不进行 HTTP 请求探测 Content-Type，不扫描启动器或完整应用列表，也没有包名兼容表或 `QUERY_ALL_PACKAGES` 权限。

候选依据系统声明的通用网页能力，因此可能包含带网页功能的非浏览器应用。缺失或非标准的能力声明可能仍导致部分应用不出现；不通过品牌包名补丁猜测接收组件。

## 系统面板

首个候选作为 `Intent.createChooser` 的主请求，其余候选通过 `EXTRA_ALTERNATE_INTENTS` 传入，保留每个候选的显式组件、原网址和匹配 MIME。没有使用存在额外入口数量限制的 `EXTRA_INITIAL_INTENTS` 来拼接完整列表。

API 29+ 在外层 chooser 设置 `EXTRA_AUTO_LAUNCH_SINGLE_CHOICE=false`，只有一个候选时也请求显示面板。如果应用侧查询没有候选，仍请求隐式系统选择器；启动失败显示简短提示。

不注册组件选择回调，不根据 chooser 自动解析的结果保存默认。原诊断用的「网页应用查询结果」Toast 及资源已删除。

## 应用内默认

Android「更多 → 外部浏览器 → 设置默认浏览器」打开带名称、图标及单选项的原生设置对话框：

- **跟随系统默认浏览器**：初始模式，发送正常的无 MIME 网页 Intent，由系统处理。
- **具体应用**：仅保存包名；打开每个新网址时重新查询该包的当前可用组件及 MIME，直接传入原网址。

只有点击「保存」才更新偏好；取消、返回或 Activity 销毁不保存，也不打开示例网址。解释文字放在自定义标题区域，避免 AlertDialog 的 message 区域遮住单选列表。Activity 销毁时关闭对话框。

新偏好文件 `browser-preferences-v1` 仅保存模式和包名，忽略旧实验偏好；不保存网址、MIME、票据或 Cookie，不改变系统全局默认。所选应用消失或启动失败时提示并恢复跟随系统；应用组件改名时可跟随重新发现的组件。

设置卡片由 Android UA 标记控制显示，桌面端保持隐藏。

## 验证与边界

- Windows / Python 3.13 完整回归：477 项通过。
- Node：成绩、成绩导入、登录网络、课表编辑四组回归通过；三个页面脚本通过 `node --check`。
- 正式 applicationId 下的 Android API 28 / 35 单元测试：84 项通过，其中浏览器相关 52 项。
- 默认流程覆盖保存后重新创建 Picker、当前地址／MIME 保留、组件更新、切换／清除、取消不保存、失效回退及对话框清理。MIME 发现覆盖去重、超过三个候选不截断及有限查询范围。
- 第 24／25 版调试 APK 构建、签名、与第 23 版证书一致，以及打包 Web UI 设置入口和诊断资源移除均已核对。安装包与本机构建工具不纳入源码提交。

用户已在上述 OPPO 真机确认第 23 版选择功能可用，截图显示 16 个候选，包含 Edge、Chrome 等。新增默认设置的进程重启保留及其他系统表现仍需真机覆盖；JVM 断言不替代系统面板或实际浏览器验证。

标准原生回归命令：在 `android/` 中运行 `gradlew testDebugUnitTest lintDebug`（Windows 使用 `gradlew.bat`）。构建环境要求见 [Android 发布说明](android-release.md)。

## 一手资料

- [按 Intent 签名声明包可见性](https://developer.android.com/training/package-visibility/declaring#intent-signature)
- [PackageManager.MATCH_ALL](https://developer.android.com/reference/android/content/pm/PackageManager#MATCH_ALL)
- [PackageManager.GET_RESOLVED_FILTER](https://developer.android.com/reference/android/content/pm/PackageManager#GET_RESOLVED_FILTER)
- [Intent.setDataAndType](https://developer.android.com/reference/android/content/Intent#setDataAndType(android.net.Uri,%20java.lang.String))
- [Intent.EXTRA_ALTERNATE_INTENTS](https://developer.android.com/reference/android/content/Intent#EXTRA_ALTERNATE_INTENTS)
- [Intent.EXTRA_AUTO_LAUNCH_SINGLE_CHOICE](https://developer.android.com/reference/android/content/Intent#EXTRA_AUTO_LAUNCH_SINGLE_CHOICE)
