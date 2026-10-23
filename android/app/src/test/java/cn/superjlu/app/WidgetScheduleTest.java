package cn.superjlu.app;

import static org.junit.Assert.*;

import java.util.Calendar;
import java.util.List;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;

@RunWith(RobolectricTestRunner.class)
public class WidgetScheduleTest {
    static final String J = "{\"v\":1,\"first_monday\":\"2026-09-07\",\"periods\":{\"1\":[\"08:00\",\"08:45\"],\"2\":[\"08:55\",\"09:40\"],\"3\":[\"10:00\",\"10:45\"]},"
            + "\"courses\":[{\"name\":\"高数\",\"location\":\"A101\",\"weekday\":4,\"start\":1,\"end\":2,\"weeks\":[1,2,3,7]},"
            + "{\"name\":\"英语\",\"location\":\"\",\"weekday\":4,\"start\":3,\"end\":3,\"weeks\":[7]},"
            + "{\"name\":\"体育\",\"weekday\":5,\"start\":1,\"end\":1,\"weeks\":[8]}]}";

    static Calendar at(int y, int m, int d, int h, int min) {
        Calendar c = Calendar.getInstance(); c.clear(); c.set(y, m - 1, d, h, min, 0); return c;
    }

    @Test public void weekAndDay() {
        WidgetSchedule s = new WidgetSchedule(J);
        assertTrue(s.valid);
        Calendar thu = at(2026, 10, 22, 7, 0); // 第7周周四
        assertEquals(7, s.weekOf(thu));
        assertEquals(4, WidgetSchedule.weekday(thu));
        List<WidgetSchedule.Item> l = s.on(thu);
        assertEquals(2, l.size());
        assertEquals("高数", l.get(0).name);
        assertEquals("08:00", l.get(0).hm(false));
        assertEquals("09:40", l.get(0).hm(true));
        assertEquals("第1-2节", l.get(0).periodText());
    }

    @Test public void remainingAndBoundary() {
        WidgetSchedule s = new WidgetSchedule(J);
        assertEquals(2, s.remainingToday(at(2026, 10, 22, 9, 0)).size());
        assertEquals(1, s.remainingToday(at(2026, 10, 22, 9, 41)).size());
        assertEquals(0, s.remainingToday(at(2026, 10, 22, 11, 0)).size());
        assertEquals(at(2026, 10, 22, 7, 45).getTimeInMillis() + 5000, s.nextBoundary(at(2026, 10, 22, 7, 0)));
        assertEquals(at(2026, 10, 22, 9, 40).getTimeInMillis() + 5000, s.nextBoundary(at(2026, 10, 22, 9, 0)));
        assertEquals(at(2026, 10, 23, 0, 0).getTimeInMillis() + 30000, s.nextBoundary(at(2026, 10, 22, 12, 0)));
    }

    @Test public void invalid() {
        assertFalse(new WidgetSchedule(null).valid);
        assertFalse(new WidgetSchedule("{bad").valid);
        assertTrue(new WidgetSchedule(null).on(Calendar.getInstance()).isEmpty());
    }

    @Test public void oemHints() {
        String[] brands = {"xiaomi redmi","huawei","honor","oppo","realme","oneplus","vivo","iqoo","samsung",
                "meizu flyme","lenovo","motorola","asus","tecno infinix","google pixel","unknownphone xyz"};
        for (String b : brands) {
            assertFalse("no intents for "+b, BackgroundHelper.autostartIntents(b).isEmpty());
            assertFalse(BackgroundHelper.hint(b).isEmpty());
            assertFalse(BackgroundHelper.brandLabel(b).isEmpty());
        }
        assertTrue(BackgroundHelper.hint("vivo vivo").contains("高耗电"));
        assertTrue(BackgroundHelper.hint("google pixel").contains("手动"));
        assertEquals("小米/红米/POCO", BackgroundHelper.brandLabel("xiaomi redmi poco"));
        assertEquals("原生 Android", BackgroundHelper.brandLabel("google pixel"));
        assertTrue(BackgroundHelper.autostartIntents("xiaomi").size() >= 3);
        assertTrue(BackgroundHelper.autostartIntents("huawei honor").size() >= 4);
        assertTrue(BackgroundHelper.autostartIntents("oppo coloros").size() >= 4);
    }

    @Test public void notifyTextSurvivesEndOfDay() {
        WidgetSchedule s = new WidgetSchedule(J);
        String[] t = s.notifyText(at(2026, 10, 22, 8, 10));
        assertEquals("高数", t[0]); assertEquals("上课中 · A101", t[1]);
        t = s.notifyText(at(2026, 10, 22, 7, 0));
        assertEquals("今天 08:00 · A101", t[1]);
        // 当天课上完后改显示下一天的课，而不是让通知消失
        t = s.notifyText(at(2026, 10, 29, 20, 0)); // 第8周周四晚 → 周五体育
        assertEquals("体育", t[0]); assertEquals("明天 08:00", t[1]);
        assertNull(s.notifyText(at(2026, 12, 1, 8, 0)));
    }

    @Test public void notificationRepostedAfterProcessDeath() {
        android.content.Context c = androidx_ctx();
        WidgetUpdater.prefs(c).edit().putBoolean(WidgetUpdater.KEY_NOTIFY, true).putString(WidgetUpdater.KEY_DATA, J).commit();
        android.app.NotificationManager nm = (android.app.NotificationManager) c.getSystemService(android.content.Context.NOTIFICATION_SERVICE);
        nm.cancelAll(); // 模拟系统在划掉 App 时清掉通知
        new WidgetReceiver().onReceive(c, new android.content.Intent(android.content.Intent.ACTION_BOOT_COMPLETED));
        org.robolectric.shadows.ShadowNotificationManager sh = org.robolectric.Shadows.shadowOf(nm);
        // 是否有课取决于当前日期，只要有近期课程就应补发；数据都在 2026 秋季
        WidgetSchedule ws = new WidgetSchedule(J);
        assertEquals(ws.notifyText(Calendar.getInstance()) != null, sh.getAllNotifications().size() == 1);
        WidgetUpdater.prefs(c).edit().putBoolean(WidgetUpdater.KEY_NOTIFY, false).commit();
        WidgetUpdater.updateAll(c);
        assertEquals(0, sh.getAllNotifications().size());
    }

    static android.content.Context androidx_ctx() { return org.robolectric.RuntimeEnvironment.getApplication(); }
}
