package cn.superjlu.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.graphics.drawable.Drawable;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;

/** App-local web default: follow the system browser, or open a chosen app. */
final class BrowserPicker {
    interface CandidateQuery {
        List<ResolveInfo> query(Intent intent, int flags);
    }

    static final int QUERY_FLAGS = PackageManager.MATCH_ALL | PackageManager.MATCH_DEFAULT_ONLY
            | PackageManager.GET_RESOLVED_FILTER;
    private static final String[] WEB_TYPES = {null, "text/html", "application/xhtml+xml"};
    /** Legacy mode from earlier builds; treated as follow-system and rewritten on read. */
    private static final String MODE_ASK = "ask";
    private static final String MODE_SYSTEM = "system";
    private static final String MODE_APP = "app";
    private final Activity activity;
    private final CandidateQuery query;
    private final SharedPreferences preferences;
    private AlertDialog settingsDialog;

    BrowserPicker(Activity activity) {
        this(activity, (intent, flags) -> activity.getPackageManager().queryIntentActivities(intent, flags));
    }

    BrowserPicker(Activity activity, CandidateQuery query) {
        this.activity = activity;
        this.query = query;
        // Separate from all old experimental preference formats; no URL, MIME or ticket is saved.
        this.preferences = activity.getSharedPreferences("browser-preferences-v1", Activity.MODE_PRIVATE);
    }

    void open(Uri uri) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        if (uri == null || !("https".equals(uri.getScheme()) || "http".equals(uri.getScheme()))) {
            Toast.makeText(activity, R.string.browser_unsupported, Toast.LENGTH_SHORT).show();
            return;
        }
        try {
            String mode = resolvedMode();
            if (MODE_APP.equals(mode)) {
                String preferred = preferences.getString("package", null);
                List<Intent> targets = findTargets(uri);
                Intent target = null;
                for (Intent candidate : targets) {
                    if (candidate.getComponent().getPackageName().equals(preferred)) {
                        target = candidate;
                        break;
                    }
                }
                if (target != null) {
                    try {
                        activity.startActivity(target);
                        return;
                    } catch (ActivityNotFoundException | SecurityException unavailable) {
                        // An app may disappear or become unavailable after discovery.
                    }
                }
                resetUnavailableDefault();
            }
            activity.startActivity(webIntent(uri, null));
        } catch (ActivityNotFoundException | SecurityException error) {
            Toast.makeText(activity, R.string.browser_open_failed, Toast.LENGTH_LONG).show();
        }
    }

    /** Follow system unless a concrete app package is saved. Legacy "ask" becomes system. */
    private String resolvedMode() {
        String mode = preferences.getString("mode", MODE_SYSTEM);
        if (MODE_ASK.equals(mode)) {
            preferences.edit().putString("mode", MODE_SYSTEM).remove("package").apply();
            return MODE_SYSTEM;
        }
        if (MODE_APP.equals(mode)) return MODE_APP;
        return MODE_SYSTEM;
    }

    private void resetUnavailableDefault() {
        preferences.edit().putString("mode", MODE_SYSTEM).remove("package").apply();
        Toast.makeText(activity, R.string.browser_default_unavailable, Toast.LENGTH_LONG).show();
    }

    private List<Intent> findTargets(Uri uri) {
        LinkedHashMap<String, Intent> targets = new LinkedHashMap<>();
        for (String type : WEB_TYPES) {
            Intent request = webIntent(uri, type);
            List<ResolveInfo> matches;
            try {
                matches = query.query(request, QUERY_FLAGS);
            } catch (SecurityException denied) {
                // Query restrictions must not prevent the system default fallback.
                continue;
            }
            if (matches == null) continue;
            for (ResolveInfo match : matches) {
                if (!isGenericWebHandler(match, uri.getScheme())) continue;
                ActivityInfo info = match.activityInfo;
                if (activity.getPackageName().equals(info.packageName)) continue;
                if (info.permission != null && !info.permission.isEmpty()
                        && activity.checkSelfPermission(info.permission) != PackageManager.PERMISSION_GRANTED) continue;
                // Prefer an untyped web entry over an HTML-only entry from the same app.
                targets.putIfAbsent(info.packageName, new Intent(request)
                        .setComponent(new ComponentName(info.packageName, info.name)));
            }
        }
        return new ArrayList<>(targets.values());
    }

    private static Intent webIntent(Uri uri, String type) {
        // setType() alone would erase the URL; keep both fields together.
        return new Intent(Intent.ACTION_VIEW).setDataAndType(uri, type)
                .addCategory(Intent.CATEGORY_BROWSABLE);
    }

    private static boolean isGenericWebHandler(ResolveInfo match, String scheme) {
        if (match == null || match.activityInfo == null) return false;
        ActivityInfo info = match.activityInfo;
        if (!info.exported || !info.enabled || info.packageName == null || info.packageName.isEmpty()
                || info.name == null || info.name.isEmpty()) return false;
        ApplicationInfo app = info.applicationInfo;
        if (app == null || !app.enabled || (app.flags & ApplicationInfo.FLAG_SUSPENDED) != 0) return false;
        // An HTML file viewer or a domain-specific deep link is not a generic web browser.
        // Inspect the matched network filter rather than trusting a MIME match alone.
        IntentFilter filter = match.filter;
        if (filter != null) {
            return filter.hasAction(Intent.ACTION_VIEW) && filter.hasCategory(Intent.CATEGORY_BROWSABLE)
                    && filter.hasDataScheme(scheme) && filter.countDataAuthorities() == 0
                    && filter.countDataPaths() == 0 && filter.countDataSchemeSpecificParts() == 0;
        }
        // Without a public matched filter we cannot establish generic network-page support.
        return false;
    }

    void showSettings() {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        close();
        PackageManager pm = activity.getPackageManager();
        List<BrowserChoice> choices = new ArrayList<>();
        choices.add(new BrowserChoice(MODE_SYSTEM, null, activity.getString(R.string.browser_follow_system),
                activity.getDrawable(android.R.drawable.ic_menu_view)));
        // A neutral network URL only queries local capability declarations; it is never opened.
        for (Intent target : findTargets(Uri.parse("https://example.org/"))) {
            String packageName = target.getComponent().getPackageName();
            CharSequence label = packageName;
            Drawable icon = pm.getDefaultActivityIcon();
            try {
                ApplicationInfo info = pm.getApplicationInfo(packageName, 0);
                label = info.loadLabel(pm);
                icon = info.loadIcon(pm);
            } catch (PackageManager.NameNotFoundException | SecurityException unavailable) {
                // Keep the discovered candidate identifiable if its label cannot be read.
            }
            choices.add(new BrowserChoice(MODE_APP, packageName, label, icon));
        }
        String mode = resolvedMode();
        String packageName = preferences.getString("package", null);
        final int[] selection = {0};
        boolean currentFound = false;
        for (int i = 0; i < choices.size(); i++) {
            BrowserChoice choice = choices.get(i);
            if (choice.mode.equals(mode) && (!MODE_APP.equals(mode) || choice.packageName.equals(packageName))) {
                selection[0] = i;
                currentFound = true;
                break;
            }
        }
        String message = activity.getString(R.string.browser_settings_hint);
        if (MODE_APP.equals(mode) && !currentFound) message = activity.getString(R.string.browser_saved_missing) + "\n\n" + message;
        int iconSize = Math.round(32 * activity.getResources().getDisplayMetrics().density);
        ArrayAdapter<BrowserChoice> adapter = new ArrayAdapter<BrowserChoice>(activity,
                android.R.layout.simple_list_item_single_choice, choices) {
            @Override public View getView(int position, View recycled, ViewGroup parent) {
                TextView row = (TextView) super.getView(position, recycled, parent);
                Drawable icon = getItem(position).icon;
                icon.setBounds(0, 0, iconSize, iconSize);
                row.setCompoundDrawablesRelative(icon, null, null, null);
                row.setCompoundDrawablePadding(iconSize / 3);
                return row;
            }
        };
        // AlertDialog's setMessage hides its choice list on Android. Keep explanatory text
        // in the title area so the radio list remains visible and fully scrollable.
        LinearLayout heading = new LinearLayout(activity);
        heading.setOrientation(LinearLayout.VERTICAL);
        int padding = Math.round(24 * activity.getResources().getDisplayMetrics().density);
        heading.setPadding(padding, padding, padding, padding / 2);
        TextView title = new TextView(activity);
        title.setTextAppearance(android.R.style.TextAppearance_Material_Title);
        title.setText(R.string.browser_settings_title);
        heading.addView(title);
        TextView explanation = new TextView(activity);
        explanation.setTextAppearance(android.R.style.TextAppearance_Material_Body1);
        explanation.setPadding(0, padding / 3, 0, 0);
        explanation.setText(message);
        heading.addView(explanation);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setCustomTitle(heading)
                .setSingleChoiceItems(adapter, selection[0], (d, which) -> selection[0] = which)
                .setPositiveButton(R.string.browser_save_default, (d, which) -> {
                    BrowserChoice choice = choices.get(selection[0]);
                    SharedPreferences.Editor edit = preferences.edit().putString("mode", choice.mode);
                    if (MODE_APP.equals(choice.mode)) edit.putString("package", choice.packageName);
                    else edit.remove("package");
                    edit.apply();
                })
                .setNegativeButton(android.R.string.cancel, null)
                .create();
        dialog.setOnDismissListener(d -> { if (settingsDialog == dialog) settingsDialog = null; });
        settingsDialog = dialog;
        dialog.show();
    }

    void close() {
        if (settingsDialog != null) settingsDialog.dismiss();
    }

    private static final class BrowserChoice {
        final String mode;
        final String packageName;
        final CharSequence label;
        final Drawable icon;

        BrowserChoice(String mode, String packageName, CharSequence label, Drawable icon) {
            this.mode = mode;
            this.packageName = packageName;
            this.label = label;
            this.icon = icon;
        }

        @Override public String toString() { return label.toString(); }
    }
}
