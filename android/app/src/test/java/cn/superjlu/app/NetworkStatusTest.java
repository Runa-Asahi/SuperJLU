package cn.superjlu.app;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = {28, 35})
public class NetworkStatusTest {
    @Test public void describesTransports() {
        assertEquals("cellular|1|0", NetworkStatus.describe(false, false, true, false, true, false));
        assertEquals("wifi|0|1", NetworkStatus.describe(false, true, false, false, false, true));
        assertEquals("wifi|1|0", NetworkStatus.describe(false, true, false, false, true, false));
        assertEquals("vpn|1|0", NetworkStatus.describe(true, true, false, false, true, false));
        assertEquals("ethernet|1|0", NetworkStatus.describe(false, false, false, true, true, false));
        assertEquals("other|0|0", NetworkStatus.describe(false, false, false, false, false, false));
    }

    @Test public void currentNeverThrows() {
        NetworkStatus.init(RuntimeEnvironment.getApplication());
        String s = NetworkStatus.current();
        assertNotNull(s);
        assertEquals(3, s.split("\\|", -1).length);
    }
}
