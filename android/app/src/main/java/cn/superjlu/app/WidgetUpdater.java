package cn.superjlu.app;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.widget.RemoteViews;

import java.util.Calendar;
import java.util.List;

/** 写入快照、刷新所有小组件和锁屏通知，并预约下一次刷新（AlarmManager，进程被杀/重启后由 WidgetReceiver 恢复）。 */
final class WidgetUpdater {
    static final String PREFS = "superjlu_widget";
    static final String KEY_DATA = "schedule_json";
    static final String KEY_NOTIFY = "lock_notify";
    static final String ACTION_TICK = "cn.superjlu.app.WIDGET_TICK";
    static final String CHANNEL = "next_class";
    static final int NOTIFY_ID = 4201;
    private static final int[] ROWS = {R.id.w_row1, R.id.w_row2, R.id.w_row3, R.id.w_row4, R.id.w_row5, R.id.w_row6};

    private WidgetUpdater() {}

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences(PREFS, Context.MODE_PRIVATE); }

    static void save(Context c, String json) {
        if (json == null || json.length() > 1_000_000) return;
        // 内容相同也要刷新：重新打开 App 时借此补发被系统清掉的通知
        if (!json.equals(prefs(c).getString(KEY_DATA, null))) prefs(c).edit().putString(KEY_DATA, json).apply();
        updateAll(c);
    }

    static void updateAll(Context ctx) {
        Context c = ctx.getApplicationContext();
        WidgetSchedule s = new WidgetSchedule(prefs(c).getString(KEY_DATA, null));
        Calendar now = Calendar.getInstance();
        AppWidgetManager m = AppWidgetManager.getInstance(c);
        int[] today = m.getAppWidgetIds(new ComponentName(c, TodayWidget.class));
        int[] week = m.getAppWidgetIds(new ComponentName(c, WeekWidget.class));
        if (today.length > 0) m.updateAppWidget(today, todayViews(c, s, now));
        if (week.length > 0) m.updateAppWidget(week, listViews(c, s, now));
        boolean notify = prefs(c).getBoolean(KEY_NOTIFY, false);
        updateNotification(c, s, now, notify);
        if (today.length + week.length > 0 || notify) schedule(c, s.valid ? s.nextBoundary(now) : now.getTimeInMillis() + 6 * 3_600_000L);
        else cancel(c);
    }

    static PendingIntent openApp(Context c) {
        Intent i = new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        return PendingIntent.getActivity(c, 1, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    static String nowWeekText(WidgetSchedule s, Calendar now) {
        if (!s.valid) return "";
        int w = s.weekOf(now);
        return (w >= 1 ? "第" + w + "周 · " : "未开学 · ") + "周" + "一二三四五六日".charAt(WidgetSchedule.weekday(now) - 1);
    }

    static RemoteViews todayViews(Context c, WidgetSchedule s, Calendar now) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_today);
        v.setOnClickPendingIntent(R.id.w_root, openApp(c));
        String[] t = s.valid ? s.notifyText(now) : null;
        v.setTextViewText(R.id.w_name, !s.valid ? "打开应用同步课表" : t == null ? "近期没有课" : t[0]);
        v.setTextViewText(R.id.w_sub, t == null ? "" : t[1]);
        return v;
    }

    static RemoteViews listViews(Context c, WidgetSchedule s, Calendar now) {
        RemoteViews v = new RemoteViews(c.getPackageName(), R.layout.widget_week);
        v.setOnClickPendingIntent(R.id.w_root, openApp(c));
        v.setTextViewText(R.id.w_title, s.valid && s.weekOf(now) >= 1 ? "第" + s.weekOf(now) + "周" : "课表");
        int r = 0;
        if (s.valid) {
            Calendar d = (Calendar) now.clone();
            for (int day = 0; day < 7 && r < ROWS.length; day++) {
                if (day > 0 && WidgetSchedule.weekday(d) == 1) break; // 只到本周日
                List<WidgetSchedule.Item> items = day == 0 ? s.remainingToday(d) : s.on(d);
                for (WidgetSchedule.Item i : items) {
                    if (r >= ROWS.length) break;
                    v.setTextViewText(ROWS[r], WidgetSchedule.dayTag(day, now) + " " + i.hm(false) + "  " + i.name + (i.location.isEmpty() ? "" : " · " + i.location));
                    v.setViewVisibility(ROWS[r], android.view.View.VISIBLE);
                    r++;
                }
                d.add(Calendar.DAY_OF_MONTH, 1);
            }
        }
        if (r == 0) {
            v.setTextViewText(ROWS[0], s.valid ? "本周没课了" : "打开应用同步课表");
            v.setViewVisibility(ROWS[0], android.view.View.VISIBLE);
            r = 1;
        }
        for (; r < ROWS.length; r++) v.setViewVisibility(ROWS[r], android.view.View.GONE);
        return v;
    }

    static void updateNotification(Context c, WidgetSchedule s, Calendar now, boolean enabled) {
        NotificationManager nm = (NotificationManager) c.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;
        String[] t = enabled && s.valid ? s.notifyText(now) : null;
        if (t == null) { nm.cancel(NOTIFY_ID); return; }
        Notification.Builder b;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "下一节课", NotificationManager.IMPORTANCE_LOW);
            ch.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            ch.setShowBadge(false);
            nm.createNotificationChannel(ch);
            b = new Notification.Builder(c, CHANNEL);
        } else {
            b = new Notification.Builder(c).setPriority(Notification.PRIORITY_LOW);
        }
        b.setSmallIcon(R.drawable.ic_launcher_foreground)
                .setContentTitle(t[0]).setContentText(t[1])
                .setOngoing(true).setShowWhen(false).setOnlyAlertOnce(true)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setContentIntent(openApp(c));
        try { nm.notify(NOTIFY_ID, b.build()); } catch (SecurityException ignored) {}
    }

    private static PendingIntent tick(Context c) {
        Intent i = new Intent(c, WidgetReceiver.class).setAction(ACTION_TICK);
        return PendingIntent.getBroadcast(c, 2, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** 不申请精确闹钟权限：setAndAllowWhileIdle 在打盹时也会触发（可能晚几分钟）。 */
    static void schedule(Context c, long at) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am == null) return;
        am.setAndAllowWhileIdle(AlarmManager.RTC, at, tick(c));
    }

    static void cancel(Context c) {
        AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE);
        if (am != null) am.cancel(tick(c));
    }
}
