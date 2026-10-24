package cn.superjlu.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Intent;
import android.content.res.Configuration;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Build;
import android.os.SystemClock;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.graphics.Color;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {
    private WebView web;
    private TranscriptChromeClient chrome;
    private BrowserPicker browsers;
    private final Handler main = new Handler(Looper.getMainLooper());
    /** 前台时每 15 分钟调一次 POST /api/session/keepalive；退到后台停止。 */
    static final long KEEPALIVE_MS = 15 * 60 * 1000L;
    /** 应用内网页打开偏好，不修改系统全局默认浏览器。 */
    static final boolean BROWSER_SETTINGS_ENABLED = true;
    private static final int LIGHT_BG = Color.parseColor("#f6f7f9");
    private static final int DARK_BG = Color.parseColor("#0e0f12");
    private static final int LIGHT_NAV = Color.parseColor("#ffffff");
    private static final int DARK_NAV = Color.parseColor("#17191e");
    /** 本地接口令牌（与 jlu_toolkit.ui.TOKEN_COOKIE / TOKEN_HEADER 一致）：同机其它 App 拿不到。 */
    static final String TOKEN_COOKIE = "superjlu_t";
    static final String TOKEN_HEADER = "X-SuperJLU-Token";
    private volatile String baseUrl;
    private volatile String authToken;
    private String barTheme = "system";
    private long lastShareMs;
    private boolean resumed;
    private final Runnable keepalive = new Runnable() {
        @Override public void run() {
            pingKeepalive();
            if (resumed) main.postDelayed(this, KEEPALIVE_MS);
        }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        NetworkStatus.init(getApplicationContext());
        setContentView(R.layout.activity_main);
        web = findViewById(R.id.web);
        applyInsets(findViewById(R.id.root));
        applyBars("system");
        web.addJavascriptInterface(new PageBridge(), "SuperJLU");
        web.setDownloadListener((url, userAgent, disposition, mime, length) -> {
            if (url == null) return;
            Uri parsed = Uri.parse(url);
            String host = parsed.getHost();
            if (!"127.0.0.1".equals(host) && !"localhost".equals(host)) return;
            if (!"/api/ics".equals(parsed.getPath())) return;
            new Thread(() -> fetchAndShare(url), "jlu-ics").start();
        });
        browsers = new BrowserPicker(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        // 原生层已按系统栏留白，网页据此不再叠加 safe-area 顶部内边距
        s.setUserAgentString(s.getUserAgentString() + " SuperJLU-Android");
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        // Without a WebChromeClient, WebView silently returns false for confirm(),
        // preventing template switches whenever there are unsaved selections.
        chrome = new TranscriptChromeClient(this);
        web.setWebChromeClient(chrome);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
                return handle(req.getUrl());
            }
            @Override
            public void onPageFinished(WebView v, String url) {
                findViewById(R.id.splash).setVisibility(View.GONE);
                web.setVisibility(View.VISIBLE);
            }
        });
        View banner = findViewById(R.id.banner);
        banner.setOnClickListener(v -> v.setVisibility(View.GONE));

        new Thread(() -> {
            try {
                ensurePython();
                com.chaquo.python.PyObject mod = Python.getInstance().getModule("jlu_android");
                String url = mod.callAttr("start", getFilesDir().getAbsolutePath(), appVersion(this)).toString();
                String token = mod.callAttr("auth_token").toString();
                authToken = token;
                baseUrl = url;
                main.post(() -> openUi(url, token));
            } catch (Throwable t) {
                main.post(() -> ((TextView) findViewById(R.id.splash_msg))
                        .setText("启动失败：" + t));
            }
        }, "jlu-start").start();

        new Thread(() -> {
            boolean ok;
            try {
                ensurePython();
                ok = Python.getInstance().getModule("jlu_android")
                        .callAttr("campus_reachable").toBoolean();
            } catch (Throwable t) { ok = false; }
            if (!ok) main.post(() -> banner.setVisibility(View.VISIBLE));
        }, "jlu-netcheck").start();
    }

    /**
     * targetSdk 35 在 Android 15 上强制 edge-to-edge：内容会画到状态栏、刘海和手势条下面。
     * 上下两块只垫颜色，高度等于系统栏，网页按钮仍留在中间，不和状态栏或手势条重叠。
     */
    @SuppressWarnings("deprecation")
    private void applyInsets(View root) {
        root.setOnApplyWindowInsetsListener((v, in) -> {
            int l, t, r, b;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets i = in.getInsets(WindowInsets.Type.systemBars()
                        | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                l = i.left; t = i.top; r = i.right; b = i.bottom;
            } else {
                l = in.getSystemWindowInsetLeft(); t = in.getSystemWindowInsetTop();
                r = in.getSystemWindowInsetRight(); b = in.getSystemWindowInsetBottom();
                if (Build.VERSION.SDK_INT >= 28 && in.getDisplayCutout() != null) {
                    t = Math.max(t, in.getDisplayCutout().getSafeInsetTop());
                }
            }
            v.setPadding(l, 0, r, 0);
            setInsetHeight(R.id.status_inset, t);
            setInsetHeight(R.id.nav_inset, b);
            return in;
        });
        root.requestApplyInsets();
    }

    private void setInsetHeight(int id, int px) {
        View bar = findViewById(id);
        if (bar == null) return;
        ViewGroup.LayoutParams lp = bar.getLayoutParams();
        if (lp.height == px) return;
        lp.height = px;
        bar.setLayoutParams(lp);
    }

    /** 系统栏跟页面底色走，浅色用深色图标。底部贴着课表导航，用卡片白而不是品牌蓝。 */
    @SuppressWarnings("deprecation")
    private void applyBars(String theme) {
        boolean dark;
        if ("dark".equals(theme)) dark = true;
        else if ("light".equals(theme)) dark = false;
        else {
            int night = getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;
            dark = night == Configuration.UI_MODE_NIGHT_YES;
        }
        paintBars(dark ? DARK_BG : LIGHT_BG, dark ? DARK_NAV : LIGHT_NAV, dark);
    }

    /**
     * 跟随系统时以网页实际解析出的颜色为准（WebView 的 prefers-color-scheme 和
     * Configuration.uiMode 在部分 ROM 上不一致，会出现上下黑边）。窗口、decor 也一起刷，
     * 避免 edge-to-edge / 手势条下露出主题默认底色。
     */
    @SuppressWarnings("deprecation")
    private void paintBars(int bg, int nav, boolean dark) {
        View root = findViewById(R.id.root);
        View status = findViewById(R.id.status_inset);
        View gesture = findViewById(R.id.nav_inset);
        if (root != null) root.setBackgroundColor(bg);
        if (status != null) status.setBackgroundColor(bg);
        if (gesture != null) gesture.setBackgroundColor(nav);
        if (web != null) web.setBackgroundColor(bg);
        Window w = getWindow();
        w.getDecorView().setBackgroundColor(bg);
        w.setStatusBarColor(bg);
        w.setNavigationBarColor(nav);
        if (Build.VERSION.SDK_INT >= 29) {
            w.setStatusBarContrastEnforced(false);
            w.setNavigationBarContrastEnforced(false);
        }
        if (Build.VERSION.SDK_INT >= 30) applyBarIcons(w, dark);
        else applyLegacyBarIcons(w, dark);
    }

    @android.annotation.TargetApi(30)
    private void applyBarIcons(Window w, boolean dark) {
        WindowInsetsController c = w.getInsetsController();
        if (c == null) return;
        int mask = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                | WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
        c.setSystemBarsAppearance(dark ? 0 : mask, mask);
    }

    @SuppressWarnings("deprecation")
    private void applyLegacyBarIcons(Window w, boolean dark) {
        if (Build.VERSION.SDK_INT < 23) return;
        int f = w.getDecorView().getSystemUiVisibility();
        if (dark) f &= ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        else f |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        if (Build.VERSION.SDK_INT >= 26) {
            if (dark) f &= ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            else f |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        }
        w.getDecorView().setSystemUiVisibility(f);
    }

    @Override public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        if ("system".equals(barTheme)) applyBars("system");
    }

    private boolean beginShare() {
        long now = SystemClock.elapsedRealtime();
        synchronized (this) {
            if (now - lastShareMs < 1500) return false;
            lastShareMs = now;
        }
        return true;
    }

    /** 先给 WebView 种本地接口令牌 Cookie（HttpOnly），再加载界面；种失败时退回 ?t= 交换。 */
    private void openUi(String url, String token) {
        CookieManager cm = CookieManager.getInstance();
        cm.setAcceptCookie(true);
        cm.setCookie(url, TOKEN_COOKIE + "=" + token + "; Path=/; HttpOnly; SameSite=Strict", ok -> {
            web.loadUrl(Boolean.TRUE.equals(ok) ? url : url + "?t=" + Uri.encode(token));
            scheduleKeepalive();
        });
    }

    /** WebView 忽略 a[download] 时的兜底：本机 /api/ics 仍拉下来交给日历。 */
    private void fetchAndShare(String url) {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(url).openConnection();
            if (authToken != null) c.setRequestProperty(TOKEN_HEADER, authToken);
            c.setInstanceFollowRedirects(false);
            c.setConnectTimeout(8000);
            c.setReadTimeout(20000);
            int code = c.getResponseCode();
            InputStream in = code >= 400 ? c.getErrorStream() : c.getInputStream();
            byte[] body = readLimited(in, 2_000_000);
            presentIcs(body);
        } catch (Exception e) {
            main.post(() -> Toast.makeText(this, "导出失败", Toast.LENGTH_LONG).show());
        } finally {
            if (c != null) c.disconnect();
        }
    }

    private static byte[] readLimited(InputStream in, int max) throws java.io.IOException {
        if (in == null) return new byte[0];
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n, total = 0;
        while ((n = in.read(buf)) >= 0) {
            total += n;
            if (total > max) throw new java.io.IOException("too large");
            out.write(buf, 0, n);
        }
        return out.toByteArray();
    }

    private void presentIcs(byte[] data) {
        if (data == null) data = new byte[0];
        String text = new String(data, StandardCharsets.UTF_8);
        if (!text.startsWith("BEGIN:VCALENDAR")) {
            String msg = "导出失败";
            try {
                String err = new JSONObject(text).optString("error");
                if (!err.isEmpty()) msg = err;
            } catch (Exception ignored) { }
            String toast = msg;
            main.post(() -> Toast.makeText(this, toast, Toast.LENGTH_LONG).show());
            return;
        }
        if (!beginShare()) return;
        try {
            File dir = new File(getCacheDir(), "exports");
            if (!dir.isDirectory() && !dir.mkdirs()) throw new java.io.IOException("mkdir");
            File out = new File(dir, "jlu-schedule.ics");
            try (FileOutputStream fos = new FileOutputStream(out)) { fos.write(data); }
            main.post(() -> openIcs(out));
        } catch (Exception e) {
            main.post(() -> Toast.makeText(this, "导出失败", Toast.LENGTH_LONG).show());
        }
    }

    private void openIcs(File out) {
        if (isDestroyed()) return;
        Uri uri = ExportProvider.uriFor(this, out);
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("text/calendar");
        send.putExtra(Intent.EXTRA_STREAM, uri);
        send.putExtra(Intent.EXTRA_SUBJECT, "吉大课表");
        send.setClipData(ClipData.newRawUri("吉大课表", uri));
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        Intent view = new Intent(Intent.ACTION_VIEW);
        view.setDataAndType(uri, "text/calendar");
        view.setClipData(ClipData.newRawUri("吉大课表", uri));
        view.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        Intent chooser = Intent.createChooser(send, "导入到日历");
        chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{view});
        try {
            startActivity(chooser);
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "没有可以打开课表的应用", Toast.LENGTH_LONG).show();
        }
    }

    public final class PageBridge {
        /** 本机版本号（APK versionName），供「版本」卡片兜底显示。 */
        @JavascriptInterface public String appVersion() { return MainActivity.appVersion(MainActivity.this); }

        @JavascriptInterface public void setBars(String theme) {
            String next = "dark".equals(theme) || "light".equals(theme) ? theme : "system";
            barTheme = next;
            main.post(() -> applyBars(next));
        }

        /** 网页把当前真正生效的底色/导航栏色发过来（含跟随系统），原生栏直接照抄。 */
        @JavascriptInterface public void setBarColors(String bg, String nav, boolean dark) {
            final int b, n;
            try {
                b = Color.parseColor(bg);
                n = Color.parseColor(nav);
            } catch (RuntimeException bad) {
                return;
            }
            main.post(() -> paintBars(b, n, dark));
        }

        /** 网页每次渲染课表时把精简快照发过来，桌面小组件读取。 */
        @JavascriptInterface public void saveWidgetData(String json) {
            try { WidgetUpdater.save(MainActivity.this, json); } catch (RuntimeException ignored) {}
        }

        @JavascriptInterface public boolean lockNotifyEnabled() {
            return WidgetUpdater.prefs(MainActivity.this).getBoolean(WidgetUpdater.KEY_NOTIFY, false);
        }

        @JavascriptInterface public void setLockNotify(boolean on) {
            WidgetUpdater.prefs(MainActivity.this).edit().putBoolean(WidgetUpdater.KEY_NOTIFY, on).apply();
            main.post(() -> {
                if (on && Build.VERSION.SDK_INT >= 33
                        && checkSelfPermission("android.permission.POST_NOTIFICATIONS") != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 42);
                }
                WidgetUpdater.updateAll(MainActivity.this);
            });
        }

        @JavascriptInterface public void requestBatteryExemption() {
            main.post(() -> BackgroundHelper.requestBatteryExemption(MainActivity.this));
        }

        @JavascriptInterface public void openAutostartSettings() {
            main.post(() -> BackgroundHelper.openAutostart(MainActivity.this));
        }

        @JavascriptInterface public String backgroundHint() {
            return BackgroundHelper.hint(BackgroundHelper.brand());
        }

        @JavascriptInterface public boolean canPinWidget() { return WidgetUpdater.canPin(MainActivity.this); }

        @JavascriptInterface public void pinWidget(int kind) {
            main.post(() -> {
                if (!WidgetUpdater.pin(MainActivity.this, kind))
                    Toast.makeText(MainActivity.this, "桌面不支持，请长按桌面添加", Toast.LENGTH_LONG).show();
            });
        }

        @JavascriptInterface public String brandLabel() {
            return BackgroundHelper.brandLabel(BackgroundHelper.brand());
        }

        @JavascriptInterface public void shareIcs(String body) {
            if (body == null || body.length() > 2_000_000) {
                main.post(() -> Toast.makeText(MainActivity.this, "导出失败", Toast.LENGTH_LONG).show());
                return;
            }
            presentIcs(body.getBytes(StandardCharsets.UTF_8));
        }
    }

    /**
     * 启动线程和网络检测线程会同时走到这里。原来两边各自 isStarted() 再 start()，
     * 两个线程都看到"未启动"时第二个会抛 IllegalStateException: Python already started。
     * 用类锁串行化，并且吞掉并发情况下仍可能出现的同一异常。
     */
    private void ensurePython() {
        synchronized (MainActivity.class) {
            if (Python.isStarted()) return;
            try {
                Python.start(new AndroidPlatform(getApplicationContext()));
            } catch (IllegalStateException e) {
                if (!Python.isStarted()) throw e;
            }
        }
    }

    private void scheduleKeepalive() {
        main.removeCallbacks(keepalive);
        if (resumed && baseUrl != null) main.postDelayed(keepalive, KEEPALIVE_MS);
    }

    /** 续期接口由 Python 侧提供；旧版本没有这个接口（404）或失败都静默忽略。 */
    private void pingKeepalive() {
        final String b = baseUrl;
        final String t = authToken;
        if (b == null) return;
        new Thread(() -> {
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(b + "api/session/keepalive").openConnection();
                if (t != null) c.setRequestProperty(TOKEN_HEADER, t);
                c.setRequestMethod("POST");
                c.setConnectTimeout(5000);
                c.setReadTimeout(30000);
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type", "application/json");
                try (OutputStream o = c.getOutputStream()) { o.write("{}".getBytes("UTF-8")); }
                c.getResponseCode();
            } catch (Exception ignored) {
            } finally {
                if (c != null) c.disconnect();
            }
        }, "jlu-keepalive").start();
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 被划掉/杀进程后系统会清掉本应用的常驻通知；回到前台时按已保存的开关补发
        try { WidgetUpdater.updateAll(this); } catch (RuntimeException ignored) {}
        resumed = true;
        if (baseUrl != null) { pingKeepalive(); scheduleKeepalive(); }
    }

    @Override
    protected void onPause() {
        resumed = false;
        main.removeCallbacks(keepalive);
        super.onPause();
    }

    @Override
    @SuppressWarnings("deprecation")
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (chrome != null && chrome.onActivityResult(requestCode, resultCode, data)) return;
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        if (requestCode == 42) WidgetUpdater.updateAll(this);
        super.onRequestPermissionsResult(requestCode, permissions, results);
    }

    @Override
    protected void onDestroy() {
        if (chrome != null) chrome.cancel();
        if (browsers != null) browsers.close();
        super.onDestroy();
    }

    /** 本机地址留在 WebView 内，其余链接交给系统浏览器。 */
    private boolean handle(Uri u) {
        if ("superjlu".equals(u.getScheme()) && "browser-settings".equals(u.getHost())) {
            if (BROWSER_SETTINGS_ENABLED) browsers.showSettings();
            return true;
        }
        String h = u.getHost();
        if ("127.0.0.1".equals(h) || "localhost".equals(h)) return false;
        browsers.open(u);
        return true;
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack(); else super.onBackPressed();
    }

    /** APK 的 versionName；拿不到时返回空串，由 Python 侧退回包内版本常量。 */
    static String appVersion(android.content.Context ctx) {
        try {
            String v = ctx.getPackageManager().getPackageInfo(ctx.getPackageName(), 0).versionName;
            return v == null ? "" : v;
        } catch (Exception e) {
            return "";
        }
    }
}
