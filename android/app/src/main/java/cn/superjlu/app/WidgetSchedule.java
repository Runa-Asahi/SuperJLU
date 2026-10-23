package cn.superjlu.app;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.TimeZone;

import org.json.JSONArray;
import org.json.JSONObject;

/** 小组件用的纯逻辑：解析网页导出的课表快照，算出某天的课和下一次刷新时间。不依赖 Android 视图，便于单测。 */
final class WidgetSchedule {
    static final class Item {
        final String name, location;
        final int weekday, start, end, startMin, endMin;
        Item(String n, String l, int wd, int s, int e, int sm, int em) {
            name = n; location = l; weekday = wd; start = s; end = e; startMin = sm; endMin = em;
        }
        String hm(boolean end) { int m = end ? endMin : startMin; return String.format("%02d:%02d", m / 60, m % 60); }
        String periodText() { return "第" + start + (end != start ? "-" + end : "") + "节"; }
    }

    private static final class Course { String name, location; int wd, s, e; int[] weeks; }

    private final List<Course> courses = new ArrayList<>();
    private final java.util.Map<Integer, int[]> periods = new java.util.HashMap<>();
    private long firstMondayDay = Long.MIN_VALUE;
    final boolean valid;

    WidgetSchedule(String json) {
        boolean ok = false;
        try {
            if (json != null && !json.isEmpty()) {
                JSONObject o = new JSONObject(json);
                String fm = o.optString("first_monday", "");
                if (fm.length() >= 10) firstMondayDay = epochDay(Integer.parseInt(fm.substring(0, 4)), Integer.parseInt(fm.substring(5, 7)), Integer.parseInt(fm.substring(8, 10)));
                JSONObject p = o.optJSONObject("periods");
                if (p != null) {
                    java.util.Iterator<String> it = p.keys();
                    while (it.hasNext()) {
                        String k = it.next();
                        JSONArray v = p.optJSONArray(k);
                        if (v == null || v.length() < 2) continue;
                        int a = toMin(v.optString(0)), b = toMin(v.optString(1));
                        try { if (a >= 0 && b > a) periods.put(Integer.parseInt(k), new int[]{a, b}); } catch (NumberFormatException ignored) {}
                    }
                }
                JSONArray cs = o.optJSONArray("courses");
                if (cs != null) for (int i = 0; i < cs.length(); i++) {
                    JSONObject c = cs.optJSONObject(i);
                    if (c == null) continue;
                    Course x = new Course();
                    x.name = c.optString("name", ""); x.location = c.optString("location", "");
                    x.wd = c.optInt("weekday"); x.s = c.optInt("start"); x.e = Math.max(x.s, c.optInt("end", x.s));
                    JSONArray w = c.optJSONArray("weeks");
                    x.weeks = new int[w == null ? 0 : w.length()];
                    for (int j = 0; j < x.weeks.length; j++) x.weeks[j] = w.optInt(j);
                    if (x.wd >= 1 && x.wd <= 7 && x.s >= 1) courses.add(x);
                }
                ok = firstMondayDay != Long.MIN_VALUE;
            }
        } catch (Exception ignored) {
            ok = false;
        }
        valid = ok;
    }

    static int toMin(String t) {
        if (t == null) return -1;
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("^(\\d{1,2}):(\\d{2})").matcher(t.trim());
        return m.find() ? Integer.parseInt(m.group(1)) * 60 + Integer.parseInt(m.group(2)) : -1;
    }

    static long epochDay(int y, int mo, int d) {
        GregorianCalendar g = new GregorianCalendar(TimeZone.getTimeZone("UTC"));
        g.clear(); g.set(y, mo - 1, d);
        return g.getTimeInMillis() / 86_400_000L;
    }

    static long epochDay(Calendar local) {
        return epochDay(local.get(Calendar.YEAR), local.get(Calendar.MONTH) + 1, local.get(Calendar.DAY_OF_MONTH));
    }

    /** 第几周（可能 ≤0 表示未开学）。 */
    int weekOf(Calendar day) {
        return (int) Math.floorDiv(epochDay(day) - firstMondayDay, 7L) + 1;
    }

    static int weekday(Calendar day) {
        int w = day.get(Calendar.DAY_OF_WEEK); // 周日=1
        return w == Calendar.SUNDAY ? 7 : w - 1;
    }

    /** 某天的课，按开始时间排序。 */
    List<Item> on(Calendar day) {
        List<Item> out = new ArrayList<>();
        if (!valid) return out;
        int wk = weekOf(day), wd = weekday(day);
        for (Course c : courses) {
            if (c.wd != wd) continue;
            boolean hit = false;
            for (int w : c.weeks) if (w == wk) { hit = true; break; }
            if (!hit) continue;
            int[] a = periods.get(c.s), b = periods.get(c.e);
            if (a == null || b == null || b[1] <= a[0]) continue;
            out.add(new Item(c.name.isEmpty() ? "未命名课程" : c.name, c.location, c.wd, c.s, c.e, a[0], b[1]));
        }
        Collections.sort(out, (x, y) -> x.startMin != y.startMin ? Integer.compare(x.startMin, y.startMin) : Integer.compare(x.endMin, y.endMin));
        return out;
    }

    /** 今天还没结束的课（正在上的排第一）。 */
    List<Item> remainingToday(Calendar now) {
        int m = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
        List<Item> out = new ArrayList<>();
        for (Item i : on(now)) if (i.endMin > m) out.add(i);
        return out;
    }

    /** 下一次需要刷新的时刻：今天某节课开始/结束，否则次日 00:00:30。 */
    long nextBoundary(Calendar now) {
        int m = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
        int best = Integer.MAX_VALUE;
        for (Item i : on(now)) {
            if (i.startMin > m && i.startMin < best) best = i.startMin;
            if (i.endMin > m && i.endMin < best) best = i.endMin;
            // 课前 15 分钟也刷新一次，「下一节」更及时
            int pre = i.startMin - 15;
            if (pre > m && pre < best) best = pre;
        }
        Calendar c = (Calendar) now.clone();
        c.set(Calendar.SECOND, 5); c.set(Calendar.MILLISECOND, 0);
        if (best != Integer.MAX_VALUE) {
            c.set(Calendar.HOUR_OF_DAY, best / 60); c.set(Calendar.MINUTE, best % 60);
        } else {
            c.add(Calendar.DAY_OF_MONTH, 1);
            c.set(Calendar.HOUR_OF_DAY, 0); c.set(Calendar.MINUTE, 0); c.set(Calendar.SECOND, 30);
        }
        return c.getTimeInMillis();
    }

    /** 7 天内的下一节（含正在上的）。返回 {dayOffset, item}，没有则 null。 */
    Object[] upcoming(Calendar now) {
        Calendar d = (Calendar) now.clone();
        for (int off = 0; off < 7; off++) {
            List<Item> l = off == 0 ? remainingToday(now) : on(d);
            if (!l.isEmpty()) return new Object[]{off, l.get(0)};
            d.add(Calendar.DAY_OF_MONTH, 1);
        }
        return null;
    }

    static String dayTag(int off, Calendar now) {
        if (off == 0) return "今天";
        if (off == 1) return "明天";
        Calendar d = (Calendar) now.clone(); d.add(Calendar.DAY_OF_MONTH, off);
        return "周" + "一二三四五六日".charAt(weekday(d) - 1);
    }

    /** 通知文案 {标题, 正文}；无课返回 null。 */
    String[] notifyText(Calendar now) {
        Object[] u = upcoming(now);
        if (u == null) return null;
        int off = (Integer) u[0]; Item i = (Item) u[1];
        int m = now.get(Calendar.HOUR_OF_DAY) * 60 + now.get(Calendar.MINUTE);
        boolean on = off == 0 && i.startMin <= m;
        String when = on ? "上课中" : dayTag(off, now) + " " + i.hm(false);
        return new String[]{i.name, when + (i.location.isEmpty() ? "" : " · " + i.location)};
    }
}
