package cn.superjlu.app;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;

/** 课表分享 JSON 的粗判与体积上限（与 Python schedule_share.MAX_BYTES 对齐）。 */
public final class ScheduleShareHelper {
    public static final String KIND = "superjlu.schedule.share";
    public static final String FILENAME = "superjlu-schedule.json";
    public static final int MAX_BYTES = 512 * 1024;
    public static final String MIME = "application/json";

    private ScheduleShareHelper() {}

    public static boolean looksLikeShare(byte[] data) {
        if (data == null || data.length < 20 || data.length > MAX_BYTES) return false;
        try {
            return looksLikeShare(new String(data, StandardCharsets.UTF_8));
        } catch (Exception e) {
            return false;
        }
    }

    public static boolean looksLikeShare(String text) {
        if (text == null) return false;
        String t = text.trim();
        if (t.length() < 20 || t.length() > MAX_BYTES) return false;
        if (!t.contains(KIND)) return false;
        try {
            JSONObject o = new JSONObject(t);
            return KIND.equals(o.optString("kind"));
        } catch (Exception e) {
            return false;
        }
    }
}
