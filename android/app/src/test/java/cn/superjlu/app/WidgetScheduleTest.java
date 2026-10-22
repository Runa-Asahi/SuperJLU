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
        assertFalse(BackgroundHelper.autostartIntents("xiaomi redmi").isEmpty());
        assertTrue(BackgroundHelper.autostartIntents("google pixel").isEmpty());
        assertTrue(BackgroundHelper.hint("vivo vivo").contains("vivo"));
        assertTrue(BackgroundHelper.hint("google").contains("加锁"));
    }
}
