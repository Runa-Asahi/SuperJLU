package cn.superjlu.app;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;

public class WeekWidget extends AppWidgetProvider {
    @Override public void onUpdate(Context c, AppWidgetManager m, int[] ids) { WidgetUpdater.updateAll(c); }
    @Override public void onEnabled(Context c) { WidgetUpdater.updateAll(c); }
    @Override public void onDisabled(Context c) { WidgetUpdater.updateAll(c); }
}
