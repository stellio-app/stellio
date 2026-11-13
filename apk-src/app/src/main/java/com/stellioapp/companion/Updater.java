package com.stellioapp.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInfo;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * Mise à jour de l'application depuis GitHub, sans passer par un store.
 * À chaque ouverture (puis au retour au premier plan si le dernier contrôle date de plus de 6 h), l'application lit
 * apk/version.json sur GitHub (écrit par la CI à chaque compilation de l'APK). Si le versionCode publié est plus récent,
 * une boîte de dialogue propose de mettre à jour : téléchargement par le gestionnaire de téléchargements d'Android,
 * vérification de la somme SHA-256, puis installation par l'installateur du système (confirmation de l'utilisateur).
 * Ne contacte que GitHub, et jamais votre serveur Stellio.
 */
final class Updater {
    static final String INFO_URL = "https://raw.githubusercontent.com/stellio-app/stellio/main/apk/version.json";
    static final String APK_URL = "https://github.com/stellio-app/stellio/raw/main/apk/stellio.apk";
    private static final long RECHECK_MS = 6L * 60 * 60 * 1000;
    private static final String FILE_NAME = "stellio-update.apk";
    private static final String APK_MIME = "application/vnd.android.package-archive";

    /** Informations publiées dans version.json. */
    static final class Info {
        int code;
        String name = "";
        String sha256 = "";
        String url = APK_URL;
    }

    private final Activity act;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private long lastCheck = 0;
    private boolean checking = false;
    private boolean asking = false;
    private Info pending;          // mise à jour acceptée, en attente de l'autorisation « sources inconnues »
    private long downloadId = -1;
    private String wantSha = "";
    private BroadcastReceiver receiver;

    Updater(Activity a) { act = a; }

    /** Contrôle au lancement de l'application. */
    void checkAtLaunch() { check(); }

    /** Au retour au premier plan : reprend une mise à jour en attente, ou recontrôle si le dernier contrôle est ancien. */
    void onResume() {
        if (pending != null && canInstall()) {
            Info p = pending;
            pending = null;
            download(p);
            return;
        }
        if (System.currentTimeMillis() - lastCheck > RECHECK_MS) check();
    }

    void destroy() {
        try { if (receiver != null) act.unregisterReceiver(receiver); } catch (Exception ignored) { }
        receiver = null;
    }

    // ── Contrôle de version ──
    private void check() {
        if (checking || asking) return;
        checking = true;
        lastCheck = System.currentTimeMillis();
        new Thread(() -> {
            Info info = null;
            try { info = fetch(); } catch (Exception ignored) { }
            checking = false;
            final Info found = info;
            if (found != null && found.code > currentCode()) ui.post(() -> ask(found));
        }, "stellio-update-check").start();
    }

    private Info fetch() throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(INFO_URL).openConnection();
        c.setConnectTimeout(8000);
        c.setReadTimeout(8000);
        c.setRequestProperty("Cache-Control", "no-cache");
        try {
            if (c.getResponseCode() != 200) return null;
            InputStream in = c.getInputStream();
            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            byte[] b = new byte[2048];
            int n;
            while ((n = in.read(b)) > 0 && buf.size() < 65536) buf.write(b, 0, n);
            JSONObject j = new JSONObject(buf.toString("UTF-8"));
            Info i = new Info();
            i.code = j.optInt("versionCode", 0);
            i.name = j.optString("versionName", "");
            i.sha256 = j.optString("sha256", "").trim().toLowerCase(Locale.ROOT);
            String u = j.optString("url", "");
            if (u.startsWith("https://github.com/") || u.startsWith("https://raw.githubusercontent.com/")) i.url = u;
            return i.code > 0 ? i : null;
        } finally {
            c.disconnect();
        }
    }

    private int currentCode() {
        try {
            PackageInfo pi = act.getPackageManager().getPackageInfo(act.getPackageName(), 0);
            return Build.VERSION.SDK_INT >= 28 ? (int) pi.getLongVersionCode() : pi.versionCode;
        } catch (Exception e) { return Integer.MAX_VALUE; }
    }

    private String currentName() {
        try { return act.getPackageManager().getPackageInfo(act.getPackageName(), 0).versionName; }
        catch (Exception e) { return ""; }
    }

    // ── Dialogue ──
    private void ask(final Info info) {
        if (act.isFinishing() || asking) return;
        asking = true;
        new AlertDialog.Builder(act)
            .setTitle(R.string.update_title)
            .setMessage(act.getString(R.string.update_msg, info.name.isEmpty() ? String.valueOf(info.code) : info.name, currentName()))
            .setPositiveButton(R.string.update_now, (d, w) -> { asking = false; start(info); })
            .setNegativeButton(R.string.update_later, (d, w) -> asking = false)
            .setOnCancelListener(d -> asking = false)
            .show();
    }

    private boolean canInstall() {
        return Build.VERSION.SDK_INT < 26 || act.getPackageManager().canRequestPackageInstalls();
    }

    private void start(Info info) {
        if (!canInstall()) {
            // Android demande d'autoriser Stellio à installer des applications ; on reprend au retour (onResume).
            pending = info;
            Toast.makeText(act, R.string.update_need_perm, Toast.LENGTH_LONG).show();
            try {
                act.startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + act.getPackageName())));
            } catch (Exception e) { pending = null; fail(); }
            return;
        }
        download(info);
    }

    // ── Téléchargement + installation ──
    private void download(Info info) {
        try {
            File old = new File(act.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), FILE_NAME);
            if (old.exists()) //noinspection ResultOfMethodCallIgnored
                old.delete();
            DownloadManager dm = (DownloadManager) act.getSystemService(Context.DOWNLOAD_SERVICE);
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(info.url))
                .setTitle("Stellio " + info.name)
                .setMimeType(APK_MIME)
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setDestinationInExternalFilesDir(act, Environment.DIRECTORY_DOWNLOADS, FILE_NAME);
            wantSha = info.sha256;
            downloadId = dm.enqueue(r);
            listen();
            Toast.makeText(act, R.string.update_downloading, Toast.LENGTH_SHORT).show();
        } catch (Exception e) { fail(); }
    }

    private void listen() {
        if (receiver != null) return;
        receiver = new BroadcastReceiver() {
            @Override public void onReceive(Context ctx, Intent intent) {
                long id = intent == null ? -1 : intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1);
                if (id == downloadId && id != -1) done(id);
            }
        };
        IntentFilter f = new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);
        if (Build.VERSION.SDK_INT >= 33) act.registerReceiver(receiver, f, Context.RECEIVER_EXPORTED);
        else act.registerReceiver(receiver, f);
    }

    private void done(final long id) {
        final DownloadManager dm = (DownloadManager) act.getSystemService(Context.DOWNLOAD_SERVICE);
        new Thread(() -> {
            boolean ok = false;
            Uri uri = null;
            Cursor c = null;
            try {
                c = dm.query(new DownloadManager.Query().setFilterById(id));
                if (c != null && c.moveToFirst()
                    && c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)) == DownloadManager.STATUS_SUCCESSFUL) {
                    uri = dm.getUriForDownloadedFile(id);
                    ok = uri != null && (wantSha.isEmpty() || wantSha.equals(sha256(uri)));
                }
            } catch (Exception ignored) {
            } finally { if (c != null) c.close(); }
            final boolean good = ok;
            final Uri apk = uri;
            ui.post(() -> {
                if (!good) { try { dm.remove(id); } catch (Exception ignored) { } fail(); return; }
                try {
                    Intent i = new Intent(Intent.ACTION_VIEW);
                    i.setDataAndType(apk, APK_MIME);
                    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                    act.startActivity(i);
                } catch (Exception e) { fail(); }
            });
        }, "stellio-update-verify").start();
    }

    private String sha256(Uri uri) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = act.getContentResolver().openInputStream(uri)) {
            if (in == null) return "";
            byte[] b = new byte[16384];
            int n;
            while ((n = in.read(b)) > 0) md.update(b, 0, n);
        }
        StringBuilder sb = new StringBuilder();
        for (byte x : md.digest()) sb.append(String.format(Locale.ROOT, "%02x", x));
        return sb.toString();
    }

    private void fail() { Toast.makeText(act, R.string.update_failed, Toast.LENGTH_LONG).show(); }
}
