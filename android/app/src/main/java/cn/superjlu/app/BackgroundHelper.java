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
 * 后台保活辅助：申请忽略电池优化 + 按厂商尝试打开自启动/后台管理页。
 * 组件名随系统版本变化，每品牌列多个候选，失败再回退电池优化列表 / 应用详情。
 * 「最近任务加锁」是系统界面上的用户操作，应用无法用代码设置。
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
        return (Build.MANUFACTURER + " " + Build.BRAND + " " + Build.MODEL).toLowerCase(Locale.ROOT);
    }

    /** 按厂商列出可能的自启动/后台/省电页面（组件名随系统版本变化，逐个尝试）。 */
    static List<Intent> autostartIntents(String brand) {
        List<Intent> out = new ArrayList<>();
        if (match(brand, "xiaomi", "redmi", "poco", "blackshark")) {
            out.add(cmp("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"));
            out.add(cmp("com.miui.securitycenter", "com.miui.powercenter.PowerSettings"));
            out.add(act("miui.intent.action.OP_AUTO_START").setPackage("com.miui.securitycenter"));
            out.add(cmp("com.miui.powerkeeper", "com.miui.powerkeeper.ui.HiddenAppsConfigActivity"));
        } else if (match(brand, "huawei", "honor")) {
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"));
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity"));
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.appcontrol.activity.StartupAppControlActivity"));
            out.add(cmp("com.huawei.systemmanager", "com.huawei.systemmanager.power.ui.HwPowerManagerActivity"));
            out.add(cmp("com.hihonor.systemmanager", "com.hihonor.systemmanager.startupmgr.ui.StartupNormalAppListActivity"));
            out.add(cmp("com.hihonor.systemmanager", "com.hihonor.systemmanager.optimize.process.ProtectActivity"));
        } else if (match(brand, "oppo", "realme", "oneplus", "coloros")) {
            out.add(cmp("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"));
            out.add(cmp("com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity"));
            out.add(cmp("com.coloros.safecenter", "com.coloros.safecenter.permission.startupapp.StartupAppListActivity"));
            out.add(cmp("com.oplus.safecenter", "com.oplus.safecenter.permission.startup.StartupAppListActivity"));
            out.add(cmp("com.oplus.battery", "com.oplus.battery.ui.BatteryMainActivity"));
            out.add(cmp("com.oneplus.security", "com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity"));
            out.add(act("com.coloros.safecenter").setPackage("com.coloros.safecenter"));
        } else if (match(brand, "vivo", "iqoo")) {
            out.add(cmp("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"));
            out.add(cmp("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"));
            out.add(cmp("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity"));
            out.add(cmp("com.vivo.abe", "com.vivo.applicationbehaviorengine.ui.ExcessivePowerManagerActivity"));
        } else if (match(brand, "samsung")) {
            out.add(cmp("com.samsung.android.lool", "com.samsung.android.sm.battery.ui.BatteryActivity"));
            out.add(cmp("com.samsung.android.sm", "com.samsung.android.sm.ui.battery.BatteryActivity"));
            out.add(cmp("com.samsung.android.sm_cn", "com.samsung.android.sm.ui.battery.BatteryActivity"));
            out.add(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        } else if (match(brand, "meizu", "flyme")) {
            out.add(cmp("com.meizu.safe", "com.meizu.safe.permission.SmartBGActivity"));
            out.add(cmp("com.meizu.safe", "com.meizu.safe.security.SHOW_APPSEC"));
            out.add(cmp("com.meizu.safe", "com.meizu.safe.powerui.PowerAppPermissionActivity"));
        } else if (match(brand, "lenovo", "motorola", "zuk")) {
            out.add(cmp("com.lenovo.security", "com.lenovo.security.purebackground.PureBackgroundActivity"));
            out.add(cmp("com.motorola.ccc", "com.motorola.ccc.settings.BatterySaverActivity"));
            out.add(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        } else if (match(brand, "asus", "zenfone")) {
            out.add(cmp("com.asus.mobilemanager", "com.asus.mobilemanager.autostart.AutoStartActivity"));
            out.add(cmp("com.asus.mobilemanager", "com.asus.mobilemanager.entry.FunctionActivity"));
            out.add(cmp("com.asus.mobilemanager", "com.asus.mobilemanager.powersaver.PowerSaverSettings"));
        } else if (match(brand, "tecno", "infinix", "itel", "transsion")) {
            out.add(cmp("com.transsion.phonemaster", "com.cyin.himgr.autostart.AutoStartActivity"));
            out.add(cmp("com.evenwell.powersaving.g3", "com.evenwell.powersaving.g3.exception.PowerSaverExceptionActivity"));
            out.add(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        } else if (match(brand, "google", "pixel", "aosp", "nothing", "fairphone")) {
            // 原生 / Pixel：没有厂商自启动页，直接给电池优化列表
            out.add(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
            out.add(new Intent(Settings.ACTION_BATTERY_SAVER_SETTINGS));
        } else {
            // 未知品牌：通用电池页
            out.add(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
            out.add(new Intent(Settings.ACTION_BATTERY_SAVER_SETTINGS));
        }
        return out;
    }

    static String hint(String brand) {
        String lock = "最近任务里加锁需手动操作。";
        if (match(brand, "xiaomi", "redmi", "poco", "blackshark")) return "开启自启动，省电策略选「无限制」。" + lock;
        if (match(brand, "huawei", "honor")) return "启动管理改为手动并全部允许。" + lock;
        if (match(brand, "oppo", "realme", "oneplus", "coloros")) return "允许自启动和后台运行。" + lock;
        if (match(brand, "vivo", "iqoo")) return "允许后台高耗电。" + lock;
        if (match(brand, "samsung")) return "后台使用限制设为「从不休眠」。" + lock;
        if (match(brand, "google", "pixel", "aosp", "nothing", "fairphone")) return "允许后台运行即可。" + lock;
        return "允许自启动和后台运行。" + lock;
    }

    /** 品牌代号，给 UI 显示「检测到：小米」之类。 */
    static String brandLabel(String brand) {
        if (match(brand, "xiaomi", "redmi", "poco", "blackshark")) return "小米/红米/POCO";
        if (match(brand, "huawei")) return "华为";
        if (match(brand, "honor")) return "荣耀";
        if (match(brand, "oppo")) return "OPPO";
        if (match(brand, "realme")) return "真我";
        if (match(brand, "oneplus")) return "一加";
        if (match(brand, "vivo")) return "vivo";
        if (match(brand, "iqoo")) return "iQOO";
        if (match(brand, "samsung")) return "三星";
        if (match(brand, "meizu", "flyme")) return "魅族";
        if (match(brand, "lenovo", "zuk")) return "联想";
        if (match(brand, "motorola")) return "摩托罗拉";
        if (match(brand, "asus")) return "华硕";
        if (match(brand, "tecno", "infinix", "itel", "transsion")) return "传音系";
        if (match(brand, "google", "pixel", "aosp", "nothing", "fairphone")) return "原生 Android";
        return "通用";
    }

    static void openAutostart(Context c) {
        for (Intent i : autostartIntents(brand())) if (start(c, i)) return;
        if (!start(c, new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))) openAppDetails(c);
    }

    static void openAppDetails(Context c) {
        start(c, new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + c.getPackageName())));
    }

    private static boolean match(String brand, String... keys) {
        for (String k : keys) if (brand.contains(k)) return true;
        return false;
    }

    private static Intent cmp(String pkg, String cls) {
        return new Intent().setComponent(new ComponentName(pkg, cls));
    }

    private static Intent act(String action) {
        return new Intent(action);
    }

    private static boolean start(Context c, Intent i) {
        if (i == null) return false;
        try {
            if (!(c instanceof android.app.Activity)) i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            c.startActivity(i);
            return true;
        } catch (ActivityNotFoundException | SecurityException e) {
            return false;
        }
    }
}
