package cn.superjlu.app;

import android.app.Application;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.pm.ProviderInfo;
import android.net.Uri;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 28)
public class ExportProviderTest {
    @Test public void exportAuthorityFollowsInstalledPackage() {
        Application app = RuntimeEnvironment.getApplication();
        for (String id : new String[]{"cn.superjlu.app", "cn.superjlu.app.local"}) {
            Context context = new ContextWrapper(app) {
                @Override public String getPackageName() { return id; }
            };
            Uri uri = ExportProvider.uriFor(context, new File("jlu-schedule.ics"));
            assertEquals(id + ".exports", uri.getAuthority());
            assertEquals("/jlu-schedule.ics", uri.getPath());
        }
    }

    @Test public void generatedManifestAndShareUriUseSameProvider() throws Exception {
        Application app = RuntimeEnvironment.getApplication();
        String authority = app.getPackageName() + ".exports";
        ProviderInfo provider = app.getPackageManager().resolveContentProvider(authority, 0);
        assertNotNull("The installed variant must own its export provider", provider);
        assertEquals(authority, provider.authority);
        assertFalse(provider.exported);
        File dir = new File(app.getCacheDir(), "exports");
        assertTrue(dir.isDirectory() || dir.mkdirs());
        File out = new File(dir, "jlu-schedule.ics");
        byte[] calendar = "BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n".getBytes(StandardCharsets.UTF_8);
        try (FileOutputStream stream = new FileOutputStream(out)) { stream.write(calendar); }
        Uri uri = ExportProvider.uriFor(app, out);
        assertEquals(authority, uri.getAuthority());
        assertEquals("text/calendar", app.getContentResolver().getType(uri));
        try (InputStream stream = app.getContentResolver().openInputStream(uri)) {
            assertNotNull(stream);
            byte[] actual = new byte[calendar.length];
            assertEquals(calendar.length, stream.read(actual));
            assertArrayEquals(calendar, actual);
        }
    }
}
