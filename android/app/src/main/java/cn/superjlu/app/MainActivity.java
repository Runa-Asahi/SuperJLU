package cn.superjlu.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.Build;
import android.view.WindowInsets;
import android.graphics.Color;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends Activity {
    private WebView web;
    private TranscriptChromeClient chrome;
    private BrowserPicker browsers;
    private final Handler main = new Handler(Looper.getMainLooper());
    /** 前台时每 15 分钟调一次 POST /api/session/keepalive；退到后台停止。 */
    static final long KEEPALIVE_MS = 15 * 60 * 1000L;
    private volatile String baseUrl;
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
        applyInsets(findViewById(R.id.root));
        web = findViewById(R.id.web);
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
                String url = Python.getInstance().getModule("jlu_android")
                        .callAttr("start", getFilesDir().getAbsolutePath()).toString();
                baseUrl = url;
                main.post(() -> { web.loadUrl(url); scheduleKeepalive(); });
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
     * 这里按系统栏 + 刘海（+ 输入法）的 insets 给根布局加内边距，WebView 顶部的按钮就不会再和状态栏重叠。
     */
    @SuppressWarnings("deprecation")
    private void applyInsets(View root) {
        getWindow().setStatusBarColor(Color.parseColor("#0B4EA2"));
        getWindow().setNavigationBarColor(Color.WHITE);
        if (Build.VERSION.SDK_INT >= 23) {
            int f = getWindow().getDecorView().getSystemUiVisibility();
            f &= ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;           // 蓝底白字的状态栏
            if (Build.VERSION.SDK_INT >= 26) f |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
            getWindow().getDecorView().setSystemUiVisibility(f);
        }
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
            v.setPadding(l, t, r, b);
            return in;
        });
        root.requestApplyInsets();
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
        if (b == null) return;
        new Thread(() -> {
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(b + "api/session/keepalive").openConnection();
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
    protected void onDestroy() {
        if (chrome != null) chrome.cancel();
        super.onDestroy();
    }

    /** 本机地址留在 WebView 内，其余链接交给系统浏览器。 */
    private boolean handle(Uri u) {
        if ("superjlu".equals(u.getScheme()) && "browser-settings".equals(u.getHost())) {
            browsers.showSettings();
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
}
