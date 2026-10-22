package cn.superjlu.app;

import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 后台保活辅助：申请忽略电池优化 + 跳到各厂商自启动/后台管理页。
 * 「最近任务加锁」是系统界面上的用户操作，应用无法用代码设置，只能给出提示。
 */
final class BackgroundHelper {
    private BackgroundHelper() {}

    static boolean ignoringBattery(Context c) {
        PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
        return pm != null && pm.isIgnoringBatteryOptimizations(c.getPackageName());
    }

    static void requestBatteryExemption(Context c) {
        if (ignoringBattery(c)) { openAppDetails(c); return; }
        Intent i = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:" + c.getPackageName()));
        if (!start(c, i) && !start(c, new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))) openAppDetails(c);
    }

    static String brand() {
        return (Build.MANUFACTURER + " " + Build.BRAND).toLowerCase(Locale.ROOT);
    }

    /** 按厂商列出可能的自启动/后台管理页面（组件名随系统版本变化，逐个尝试）。 */
    static List<Intent> autostartIntents(String brand) {
        List<Intent> out = new ArrayList<>();
        if (brand.contains("xiaomi") || brand.contains("redmi") || brand.contains("poco")) {
            out.add(cmp("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"));
        } else if (brand.contains("huawei") || brand.contains("honor")) {
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"));
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity"));
            out.add(cmp("com.hihonor.systemmanager", "com.hihonor.systemmanager.startupmgr.ui.StartupNormalAppListActivity"));
        } else if (brand.contains("oppo") || brand.contains("realme") || brand.contains("oneplus")) {
            out.add(cmp("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"));
            out.add(cmp("com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity"));
            out.add(cmp("com.oplus.safecenter", "com.oplus.safecenter.permission.startup.StartupAppListActivity"));
        } else if (brand.contains("vivo") || brand.contains("iqoo")) {
            out.add(cmp("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"));
            out.add(cmp("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"));
        } else if (brand.contains("samsung")) {
            out.add(cmp("com.samsung.android.lool", "com.samsung.android.sm.battery.ui.BatteryActivity"));
        }
        return out;
    }

    static String hint(String brand) {
        String lock = "在最近任务里给 SuperJLU 加锁（应用无法代为设置）";
        if (brand.contains("xiaomi") || brand.contains("redmi") || brand.contains("poco"))
            return "小米/红米：开启「自启动」，省电策略选「无限制」；" + lock + "：最近任务中长按卡片 → 锁定。";
        if (brand.contains("huawei") || brand.contains("honor"))
            return "华为/荣耀：应用启动管理里改为「手动管理」并全部允许；" + lock + "：最近任务中下拉卡片。";
        if (brand.contains("oppo") || brand.contains("realme") || brand.contains("oneplus"))
            return "OPPO/一加/真我：允许「自启动」和「后台运行」；" + lock + "：最近任务卡片右上角菜单 → 锁定。";
        if (brand.contains("vivo") || brand.contains("iqoo"))
            return "vivo/iQOO：后台耗电管理里选「允许后台高耗电」；" + lock + "：最近任务中下拉卡片。";
        if (brand.contains("samsung"))
            return "三星：电池 → 后台使用限制里把 SuperJLU 设为「从不休眠」；" + lock + "：最近任务中点图标 → 保持打开。";
        return "允许后台运行/自启动，并" + lock + "。";
    }

    static void openAutostart(Context c) {
        for (Intent i : autostartIntents(brand())) if (start(c, i)) return;
        openAppDetails(c);
    }

    static void openAppDetails(Context c) {
        start(c, new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + c.getPackageName())));
    }

    private static Intent cmp(String pkg, String cls) {
        return new Intent().setComponent(new ComponentName(pkg, cls));
    }

    private static boolean start(Context c, Intent i) {
        try {
            if (!(c instanceof android.app.Activity)) i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
            return true;
        } catch (ActivityNotFoundException | SecurityException e) {
            return false;
        }
    }
}
