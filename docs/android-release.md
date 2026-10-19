# Android 发布约定（给 `android/` Gradle 项目）

CI：`.github/workflows/release-android.yml`。推 `v*` 标签 → 签名 release apk 上传到同名 Release（与 Windows exe 共用）；手动运行 → 未签名 debug apk 作为 Actions 产物。

## Gradle 项目需要满足

1. `android/gradlew`（含 wrapper jar）存在；CI 在 `android/` 下执行 `./gradlew assembleRelease` / `assembleDebug`。没有 `android/gradlew` 时工作流直接跳过并提示。
2. 应用模块名为 `app`，产物路径：
   - release：`android/app/build/outputs/apk/release/*.apk`（**不签名**，即 `app-release-unsigned.apk`；不要在 Gradle 里配置 `signingConfig`，签名由 CI 用 apksigner 完成）
   - debug：`android/app/build/outputs/apk/debug/app-debug.apk`
3. 单一 apk（不做 ABI split）；如要 split，先跟 Asahi 说，CI 需要改成多文件。
4. 版本号从环境变量读取，本地缺省时给默认值：
   ```kotlin
   versionName = System.getenv("JLU_VERSION_NAME") ?: "0.0.0-dev"   // = jlu_toolkit.__version__
   versionCode = (System.getenv("JLU_VERSION_CODE") ?: "1").toInt()  // = GitHub run number，单调递增
   ```
5. JDK 17、SDK platform 35（build-tools 35.0.0）、Chaquopy 16.1、CI 用 `android-actions/setup-android` 的最新 build-tools；Chaquopy `buildPython` 用 CI 里的 Python 3.13（`python3` 在 PATH 上）。
6. 签名：CI 从 secrets `ANDROID_KEYSTORE_B64 / ANDROID_KEYSTORE_PASSWORD / ANDROID_KEY_ALIAS / ANDROID_KEY_PASSWORD` 还原 PKCS12 keystore（别名 `jlu-toolkit`，RSA 4096，30 年）。Gradle 不需要读这些变量。

## 文件导入的原生回归

在 `android/` 下运行 `./gradlew testDebugUnitTest`（Windows 使用 `gradlew.bat`）。
首次运行需要下载 Robolectric 及 Android 测试运行库；测试依赖不打进 APK。

`TranscriptChromeClientTest` 在 API 28 / 35 上验证系统文件选择器的调用、content URI 回传、
取消后重选、连续请求、Activity 销毁时释放回调、ClipData，以及选择器缺失时的回退和提示。
测试使用虚构 URI，不启动 Python 服务或读取真实账号、成绩文件。

`WebView` 的文件输入必须由 `WebChromeClient.onShowFileChooser` 接入；仅设置一个默认
`WebChromeClient` 会取消文件请求。实现使用系统文档选择器，不需要存储权限。
部分教务导出文件的 MIME 类型不准确，所以选择器不按 MIME 隐藏文件，扩展名和 5 MB
大小限制继续由网页、后端校验。参见 [Android 文件选择回调](https://developer.android.com/reference/android/webkit/WebChromeClient#onShowFileChooser(android.webkit.WebView,android.webkit.ValueCallback,android.webkit.WebChromeClient.FileChooserParams))。

发布前仍应在真机上检查：选择下载目录内的 XLSX / XLS / CSV、取消后重选、未登录时导入，
以及未保存修改时切换模板的确认弹窗。JVM 回归不能替代不同厂商文件管理器的实际验证。

## 网络与外部浏览器回归

同一 `testDebugUnitTest` 还运行 `BrowserPickerTest` 和 `SchoolHttpTest`（API 28 / 35）。
指定浏览器暂未实现、按钮禁用。前者只验证占位边界：外链使用系统默认、忽略旧实验偏好、
接口不弹选择器或全局设置、不支持的链接被拒绝，以及启动失败提示；后者以虚构连接验证
系统 HTTPS 单跳的请求体、多个 Cookie、重定向/错误状态与连接释放，不调用真实认证。
需要在真机上验证 Python → Java 的 Chaquopy 桥、家庭 Wi-Fi/流量下的真实登录同步，
以及正常外链默认打开、浏览器选择按钮不可用。参见 [校外连接说明](offcampus-network.md)。

local.19 在 OPPO Find X8 Ultra / ColorOS 16 / Android 16 上未弹窗，local.20 又列出全部应用。
按用户要求，local.21 删除选择算法，仅保留 UI 与接口占位。后续 PR 必须列出
[浏览器选择 TODO](TODO-browser-selection.md)，由后续贡献者研究和真机验证后再启用。

教务采用手动「校园网直连／校外 WebVPN」，不再自动探测并切换路由。真机需分别验证校园网
直连、流量及家庭 Wi-Fi 下 WebVPN 登录同步，以及取消切换时保留原通道和账号会话。
换网但未切换方式时，查询失败应显示简短提示和检查登录方式入口，不输出原始端点清单；
空教室上次查询结果应保留，点击入口只能导航到登录卡片，不能自动切换路由。
网络失败时保留缓存，不得把连接问题当成账号过期。学校 OA 原站可经校园网或学校 VPN 访问；应用内选择「校外 WebVPN」后 OA 同步也会走应用内 VPN，浏览器 WebVPN 登录不会自动接通程序会话。WinHTTP 12029 等校外真实会话仍须真机分别验证。

## Chaquopy 与 cryptography

`secure_store` 在 Android 下用 Android Keystore（别名 `jlu-toolkit-storage`，AES/GCM/NoPadding）包裹 32 字节主密钥，
包裹后的密钥存 `<config>/storage-key.wrapped`；数据仍是 AES-256-GCM 的 `.enc`（格式不变），需要 `cryptography`。
`cryptography` 是原生扩展，必须用 Chaquopy 仓库提供的 wheel（https://chaquo.com/pypi-13.1/cryptography/），目前最新为 **42.0.8**（cp38–cp313，arm64-v8a / x86_64 等）：

```kotlin
chaquopy { defaultConfig { pip {
    install("cryptography==42.0.8")
    install("..")            // 或安装 jlu_toolkit 源码 / wheel
} } }
```

不要在 Android 上装 `keyring`（用不到）。Python 侧通过 `from java import jclass` 自动识别 Chaquopy，`secure_store.backend_name()` 返回 `android-keystore`。
