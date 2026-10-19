package cn.superjlu.app;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;
import org.robolectric.shadows.ShadowToast;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 35})
public class BrowserPickerTest {
    public static class CaptureActivity extends Activity {
        Intent opened;
        boolean missing;
        boolean denied;
        @Override public void startActivity(Intent intent) {
            if (missing) throw new ActivityNotFoundException();
            if (denied) throw new SecurityException();
            opened = intent;
        }
        @Override public void startActivityForResult(Intent intent, int code) {
            fail("Disabled feature must not open an application picker");
        }
    }
    private CaptureActivity activity;
    private BrowserPicker browsers;

    @Before public void setup() {
        activity = Robolectric.buildActivity(CaptureActivity.class).setup().get();
        browsers = new BrowserPicker(activity);
    }

    @Test public void externalLinksIgnoreAllExperimentalSavedBrowserPreferences() {
        activity.getSharedPreferences("external-browser", 0).edit()
                .putString("selected", "test.old").putString("selected_component", "test.old/.Browser")
                .putString("selected_package", "test.old").commit();
        Uri uri = Uri.parse("https://example.invalid/page?value=1");
        browsers.open(uri);
        assertEquals(Intent.ACTION_VIEW, activity.opened.getAction());
        assertEquals(uri, activity.opened.getData());
        assertNull(activity.opened.getPackage());
        assertNull(activity.opened.getComponent());
        assertNull(activity.opened.getType());
    }

    @Test public void reservedSettingsInterfaceCannotOpenPickerOrGlobalSettings() {
        browsers.showSettings();
        assertNull(activity.opened);
        assertTrue(ShadowToast.getTextOfLatestToast().contains("暂不可用"));
    }

    @Test public void browserSettingsEntryIsTemporarilyOffline() {
        // 「更多 → 外部浏览器」暂时下线；恢复前需满足 docs/TODO-browser-selection.md 的验收要求。
        assertFalse(MainActivity.BROWSER_SETTINGS_ENABLED);
    }

    @Test public void unsupportedLinksAreNotSentToOtherApplications() {
        browsers.open(Uri.parse("file:///data/private/account"));
        assertNull(activity.opened);
    }

    @Test public void missingDefaultHandlerReportsFailureWithoutOpeningPicker() {
        activity.missing = true;
        browsers.open(Uri.parse("https://example.invalid/"));
        assertNull(activity.opened);
        assertTrue(ShadowToast.getTextOfLatestToast().contains("无法打开网页"));
    }

    @Test public void deniedDefaultHandlerReportsFailureWithoutOpeningSettings() {
        activity.denied = true;
        browsers.open(Uri.parse("https://example.invalid/"));
        assertNull(activity.opened);
        assertTrue(ShadowToast.getTextOfLatestToast().contains("无法打开网页"));
    }
}
