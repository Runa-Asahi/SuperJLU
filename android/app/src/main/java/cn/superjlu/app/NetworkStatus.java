package cn.superjlu.app;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;

/**
 * 只读：报告系统当前默认网络走的是 Wi-Fi 还是移动数据、是否通过系统联网验证。
 * 供 Python 侧在「校园网直连」模式下解释直连失败的常见原因。
 * 不切换路由、不绑定 socket、不请求额外权限（ACCESS_NETWORK_STATE 已在清单中）。
 */
public final class NetworkStatus {
    private static volatile Context app;

    private NetworkStatus() {}

    public static void init(Context context) {
        if (context != null) app = context.getApplicationContext();
    }

    /** 返回 "transport|validated|captive"，例如 "cellular|1|0"；拿不到时返回 "unknown|0|0"。 */
    public static String current() {
        Context c = app;
        if (c == null) return "unknown|0|0";
        try {
            ConnectivityManager cm = (ConnectivityManager) c.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (cm == null) return "unknown|0|0";
            Network n = cm.getActiveNetwork();
            if (n == null) return "none|0|0";
            NetworkCapabilities caps = cm.getNetworkCapabilities(n);
            if (caps == null) return "unknown|0|0";
            return describe(
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN),
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI),
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR),
                    caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET),
                    caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED),
                    caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL));
        } catch (RuntimeException e) {
            return "unknown|0|0";
        }
    }

    static String describe(boolean vpn, boolean wifi, boolean cellular, boolean ethernet,
                           boolean validated, boolean captive) {
        String t = vpn ? "vpn" : wifi ? "wifi" : cellular ? "cellular" : ethernet ? "ethernet" : "other";
        return t + "|" + (validated ? "1" : "0") + "|" + (captive ? "1" : "0");
    }
}
