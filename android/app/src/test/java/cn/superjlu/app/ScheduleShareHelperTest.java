package cn.superjlu.app;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class ScheduleShareHelperTest {
    private static final String SAMPLE = "{"
            + "\"kind\":\"superjlu.schedule.share\","
            + "\"version\":1,"
            + "\"term\":\"2026-2027-1\","
            + "\"first_monday\":\"2026-09-07\","
            + "\"periods\":{\"1\":[\"08:00\",\"08:45\"]},"
            + "\"courses\":[{\"name\":\"高等数学\",\"teacher\":\"王\",\"location\":\"A\","
            + "\"weekday\":1,\"start\":1,\"end\":2,\"weeks\":[1,2]}]"
            + "}";

    @Test public void acceptsShareDocument() {
        assertTrue(ScheduleShareHelper.looksLikeShare(SAMPLE));
        assertTrue(ScheduleShareHelper.looksLikeShare(SAMPLE.getBytes(StandardCharsets.UTF_8)));
    }

    @Test public void rejectsNonShareOrHuge() {
        assertFalse(ScheduleShareHelper.looksLikeShare("{\"kind\":\"nope\"}"));
        assertFalse(ScheduleShareHelper.looksLikeShare("{"));
        assertFalse(ScheduleShareHelper.looksLikeShare((String) null));
        byte[] huge = new byte[ScheduleShareHelper.MAX_BYTES + 8];
        assertFalse(ScheduleShareHelper.looksLikeShare(huge));
    }

    @Test public void exportProviderServesJsonMime() throws Exception {
        android.app.Application app = RuntimeEnvironment.getApplication();
        File dir = new File(app.getCacheDir(), "exports");
        assertTrue(dir.isDirectory() || dir.mkdirs());
        File out = new File(dir, ScheduleShareHelper.FILENAME);
        try (FileOutputStream stream = new FileOutputStream(out)) {
            stream.write(SAMPLE.getBytes(StandardCharsets.UTF_8));
        }
        android.net.Uri uri = ExportProvider.uriFor(app, out);
        assertEquals("application/json", app.getContentResolver().getType(uri));
        assertEquals("/" + ScheduleShareHelper.FILENAME, uri.getPath());
    }
}
