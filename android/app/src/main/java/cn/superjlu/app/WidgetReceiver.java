package cn.superjlu.app;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

/** 闹钟到点、开机、改时间/时区、应用更新后重新刷新小组件并续约闹钟。 */
public class WidgetReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        try { WidgetUpdater.updateAll(context); } catch (RuntimeException ignored) {}
    }
}
