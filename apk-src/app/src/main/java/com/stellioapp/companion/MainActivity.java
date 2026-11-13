package com.stellioapp.companion;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.Manifest;
import android.app.DownloadManager;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.PermissionRequest;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import com.google.mlkit.vision.barcode.common.Barcode;
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions;
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning;

import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Stellio Companion : ouvre un serveur Stellio (Raspberry Pi / LXC) dans une WebView plein écran.
 * Deux adresses possibles : interne (réseau local) et externe (accès distant). L'application essaie d'abord l'interne,
 * sinon l'externe, et bascule toute seule de l'une à l'autre quand le réseau change (contrôle toutes les 20 s).
 * Liaison par QR code : stellio://connect?local=…&remote=… (scanner intégré ou appareil photo du téléphone).
 */
public class MainActivity extends Activity {
    private static final String PREFS = "stellio";
    private static final String KEY_LOCAL = "local";
    private static final String KEY_REMOTE = "remote";
    private static final int REQ_FILE = 4711;
    private static final int REQ_CAM_FILE = 4712;
    private static final int REQ_CAM_WEB = 4713;
    private static final long RETRY_MS = 8000;
    private static final long MONITOR_MS = 20000;

    private final Handler ui = new Handler(Looper.getMainLooper());
    private final AtomicBoolean resolving = new AtomicBoolean(false);
    private FrameLayout root;
    private WebView web;
    private View setupView;
    private View offlineView;
    private EditText localInput;
    private EditText remoteInput;
    private TextView setupStatus;
    private TextView offlineAddr;
    private Button connectBtn;

    private String local = "";      // adresse interne, sans « / » final
    private String remote = "";     // adresse externe
    private String current = "";    // adresse actuellement chargée
    private int fails = 0;
    private boolean pageFailed = false;
    private long lastBack = 0;
    private ValueCallback<Uri[]> filePathCallback;
    private WebChromeClient.FileChooserParams pendingParams;
    private PermissionRequest pendingWebPerm;
    private Uri cameraUri;
    private boolean cameraAsked = false;
    private ConnectivityManager.NetworkCallback netCallback;

    private final Runnable retryTask = new Runnable() {
        @Override public void run() { if (visible(offlineView)) { reach(true); ui.postDelayed(this, RETRY_MS); } }
    };
    private final Runnable monitorTask = new Runnable() {
        @Override public void run() { if (visible(web)) reach(false); ui.postDelayed(this, MONITOR_MS); }
    };
    private final Runnable netTask = new Runnable() {
        @Override public void run() { if (!visible(setupView)) reach(visible(offlineView)); }
    };

    private static boolean visible(View v) { return v != null && v.getVisibility() == View.VISIBLE; }

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        root = new FrameLayout(this);
        root.setBackgroundColor(getColor(R.color.bg));
        root.setFitsSystemWindows(true);
        setContentView(root);
        buildWebView();
        buildSetup();
        buildOffline();
        local = getSharedPreferences(PREFS, MODE_PRIVATE).getString(KEY_LOCAL, "");
        remote = getSharedPreferences(PREFS, MODE_PRIVATE).getString(KEY_REMOTE, "");
        registerNetworkMonitor();
        if (handleLink(getIntent() == null ? null : getIntent().getDataString())) return;
        if (local.isEmpty() && remote.isEmpty()) showSetup(); else { showWeb(); reach(true); }
        ui.postDelayed(monitorTask, MONITOR_MS);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleLink(intent == null ? null : intent.getDataString());
    }

    // ── Interface (construite en code, sans fichiers de mise en page) ──
    private int dp(int v) { return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, getResources().getDisplayMetrics()); }

    private TextView text(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextSize(sp); t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        return t;
    }

    private Button button(String label, boolean primary) {
        Button bt = new Button(this);
        bt.setText(label); bt.setAllCaps(false); bt.setTextColor(primary ? Color.WHITE : getColor(R.color.text));
        bt.setBackgroundColor(primary ? getColor(R.color.accent) : getColor(R.color.card));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52));
        lp.topMargin = dp(12);
        bt.setLayoutParams(lp);
        return bt;
    }

    private LinearLayout column(int gravity) {
        LinearLayout c = new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setGravity(gravity);
        c.setPadding(dp(24), dp(24), dp(24), dp(24));
        return c;
    }

    private EditText input(String hint) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setHintTextColor(getColor(R.color.muted));
        e.setTextColor(getColor(R.color.text));
        e.setSingleLine(true);
        e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        return e;
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void buildWebView() {
        web = new WebView(this);
        web.setLayoutParams(new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        web.setBackgroundColor(getColor(R.color.bg));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);   // serveur en http local
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setSupportZoom(false);
        s.setUserAgentString(s.getUserAgentString() + " StellioCompanion/1.0.7");
        CookieManager cm = CookieManager.getInstance();
        cm.setAcceptCookie(true);
        cm.setAcceptThirdPartyCookies(web, false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if (isOwnHost(u) || "about".equals(u.getScheme())) return false;
                if ("http".equals(u.getScheme()) || "https".equals(u.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) { }
                }
                return true;
            }
            @Override public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame()) { pageFailed = true; showOffline(); }
            }
            @Override public void onReceivedHttpError(WebView v, WebResourceRequest r, WebResourceResponse e) {
                if (r.isForMainFrame() && e.getStatusCode() >= 500) { pageFailed = true; showOffline(); }
            }
            @Override public void onPageFinished(WebView v, String url) {
                if (!pageFailed && !visible(setupView)) showWeb();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb, FileChooserParams p) {
                if (filePathCallback != null) filePathCallback.onReceiveValue(null);
                filePathCallback = cb;
                pendingParams = p;
                if (acceptsImage(p) && !hasCamera() && !cameraAsked) {
                    cameraAsked = true;      // une seule demande ; en cas de refus, seule la galerie est proposée
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAM_FILE);
                    return true;
                }
                return launchChooser();
            }
            // Caméra demandée par la page elle-même (getUserMedia, uniquement sur une adresse https)
            @Override public void onPermissionRequest(PermissionRequest req) {
                runOnUiThread(() -> {
                    boolean video = false;
                    for (String r : req.getResources()) if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) video = true;
                    if (!video || !isOwnHost(req.getOrigin())) { req.deny(); return; }
                    if (hasCamera()) req.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
                    else { pendingWebPerm = req; requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAM_WEB); }
                });
            }
        });
        web.setDownloadListener((url, ua, cd, mime, len) -> {
            try {
                DownloadManager.Request req = new DownloadManager.Request(Uri.parse(url));
                String name = URLUtil.guessFileName(url, cd, mime);
                String cookie = CookieManager.getInstance().getCookie(url);
                if (cookie != null) req.addRequestHeader("Cookie", cookie);
                req.addRequestHeader("User-Agent", ua);
                req.setMimeType(mime);
                req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                req.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
                ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(req);
                Toast.makeText(this, name, Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                try { startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); } catch (Exception ignored) { }
            }
        });
        root.addView(web);
    }

    private void buildSetup() {
        LinearLayout c = column(Gravity.TOP);
        c.addView(text(getString(R.string.setup_title), 22, getColor(R.color.text), true));
        TextView note = text(getString(R.string.edition_note), 13, getColor(R.color.muted), false);
        note.setPadding(0, dp(6), 0, dp(10));
        c.addView(note);
        TextView help = text(getString(R.string.setup_help), 13, getColor(R.color.muted), false);
        help.setPadding(0, 0, 0, dp(16));
        c.addView(help);
        Button scan = button(getString(R.string.scan_qr), false);
        scan.setOnClickListener(v -> scanQr());
        c.addView(scan);
        TextView l1 = text(getString(R.string.local_label), 13, getColor(R.color.muted), false);
        l1.setPadding(0, dp(18), 0, 0);
        c.addView(l1);
        localInput = input(getString(R.string.local_hint));
        c.addView(localInput);
        TextView l2 = text(getString(R.string.remote_label), 13, getColor(R.color.muted), false);
        l2.setPadding(0, dp(12), 0, 0);
        c.addView(l2);
        remoteInput = input(getString(R.string.remote_hint));
        c.addView(remoteInput);
        connectBtn = button(getString(R.string.connect), true);
        connectBtn.setOnClickListener(v -> saveAndConnect());
        c.addView(connectBtn);
        setupStatus = text("", 13, Color.parseColor("#E85D75"), false);
        setupStatus.setPadding(0, dp(12), 0, 0);
        c.addView(setupStatus);
        ScrollView sv = new ScrollView(this);
        sv.setFillViewport(true);
        sv.setBackgroundColor(getColor(R.color.bg));
        sv.setLayoutParams(new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        sv.addView(c);
        setupView = sv;
        root.addView(sv);
    }

    private void buildOffline() {
        LinearLayout c = column(Gravity.CENTER);
        c.setBackgroundColor(getColor(R.color.bg));
        c.setLayoutParams(new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        c.addView(text(getString(R.string.offline_title), 22, getColor(R.color.text), true));
        TextView t = text(getString(R.string.offline_text), 14, getColor(R.color.muted), false);
        t.setGravity(Gravity.CENTER);
        t.setPadding(0, dp(10), 0, dp(10));
        c.addView(t);
        offlineAddr = text("", 13, getColor(R.color.text), false);
        offlineAddr.setGravity(Gravity.CENTER);
        offlineAddr.setPadding(0, 0, 0, dp(10));
        c.addView(offlineAddr);
        Button retry = button(getString(R.string.retry), true);
        retry.setOnClickListener(v -> reach(true));
        c.addView(retry);
        Button edit = button(getString(R.string.edit_addresses), false);
        edit.setOnClickListener(v -> showSetup());
        c.addView(edit);
        offlineView = c;
        root.addView(c);
    }

    // ── Affichage ──
    private void showWeb() { setupView.setVisibility(View.GONE); offlineView.setVisibility(View.GONE); web.setVisibility(View.VISIBLE); ui.removeCallbacks(retryTask); }

    private void showSetup() {
        web.setVisibility(View.GONE); offlineView.setVisibility(View.GONE); setupView.setVisibility(View.VISIBLE);
        localInput.setText(local); remoteInput.setText(remote); setupStatus.setText("");
        ui.removeCallbacks(retryTask);
    }

    private void showOffline() {
        if (visible(setupView)) return;
        StringBuilder sb = new StringBuilder();
        if (!local.isEmpty()) sb.append(getString(R.string.addr_local)).append(" : ").append(local).append('\n');
        if (!remote.isEmpty()) sb.append(getString(R.string.addr_remote)).append(" : ").append(remote);
        offlineAddr.setText(sb.toString().trim());
        web.setVisibility(View.GONE); offlineView.setVisibility(View.VISIBLE);
        ui.removeCallbacks(retryTask); ui.postDelayed(retryTask, RETRY_MS);
    }

    // ── Choix de l'adresse : interne d'abord, sinon externe ──
    private boolean isOwnHost(Uri u) {
        String h = u.getHost();
        if (h == null) return false;
        for (String base : new String[]{local, remote}) {
            if (base.isEmpty()) continue;
            Uri b = Uri.parse(base);
            if (h.equalsIgnoreCase(b.getHost()) && u.getPort() == b.getPort()) return true;
        }
        return false;
    }

    /** Cherche l'adresse joignable (en tâche de fond) puis charge ou bascule. `forceReload` : recharge même si l'adresse ne change pas. */
    private void reach(final boolean forceReload) {
        if (local.isEmpty() && remote.isEmpty()) { showSetup(); return; }
        if (!resolving.compareAndSet(false, true)) return;
        final String l = local, r = remote;
        new Thread(() -> {
            String best = null;
            if (!l.isEmpty() && isStellio(l, 2500)) best = l;
            else if (!r.isEmpty() && isStellio(r, 6000)) best = r;
            final String pick = best;
            ui.post(() -> { resolving.set(false); onReach(pick, forceReload); });
        }).start();
    }

    private void onReach(String pick, boolean forceReload) {
        if (visible(setupView)) return;
        boolean wasOffline = visible(offlineView);
        if (pick == null) {
            fails++;
            if (wasOffline || fails >= 2 || current.isEmpty()) showOffline();
            return;
        }
        fails = 0;
        if (pick.equals(current) && !wasOffline && !forceReload) return;
        boolean switched = !current.isEmpty() && !pick.equals(current);
        current = pick;
        pageFailed = false;
        web.loadUrl(pick + "/");
        if (switched) Toast.makeText(this, pick.equals(local) ? R.string.to_local : R.string.to_remote, Toast.LENGTH_SHORT).show();
    }

    /** Un serveur Stellio sert /manifest.json (PWA) qui contient « Stellio ». */
    private static boolean isStellio(String base, int timeoutMs) {
        HttpURLConnection c = null;
        try {
            c = (HttpURLConnection) new URL(base + "/manifest.json").openConnection();
            c.setConnectTimeout(timeoutMs); c.setReadTimeout(timeoutMs);
            if (c.getResponseCode() != 200) return false;
            byte[] buf = new byte[4096];
            int n = c.getInputStream().read(buf);
            return n > 0 && new String(buf, 0, n, "UTF-8").toLowerCase(Locale.ROOT).contains("stellio");
        } catch (Exception e) {
            return false;
        } finally {
            if (c != null) c.disconnect();
        }
    }

    // ── Saisie des adresses, QR code ──
    /** Retourne l'adresse nettoyée, "" si vide, null si invalide. */
    private static String normalize(String raw) {
        String s = raw == null ? "" : raw.trim();
        if (s.isEmpty()) return "";
        if (s.contains(" ")) return null;
        String low = s.toLowerCase(Locale.ROOT);
        if (!low.startsWith("http://") && !low.startsWith("https://")) s = "http://" + s;
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        try {
            Uri u = Uri.parse(s);
            return (u.getHost() == null || u.getHost().isEmpty()) ? null : s;
        } catch (Exception e) {
            return null;
        }
    }

    private void saveAddresses(String l, String r) {
        local = l; remote = r; current = ""; fails = 0;
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(KEY_LOCAL, l).putString(KEY_REMOTE, r).apply();
    }

    private void saveAndConnect() {
        final String l = normalize(localInput.getText().toString());
        final String r = normalize(remoteInput.getText().toString());
        setupStatus.setTextColor(Color.parseColor("#E85D75"));
        if (l == null || r == null) { setupStatus.setText(R.string.bad_url); return; }
        if (l.isEmpty() && r.isEmpty()) { setupStatus.setText(R.string.need_one); return; }
        connectBtn.setEnabled(false);
        setupStatus.setTextColor(getColor(R.color.muted));
        setupStatus.setText(R.string.connecting);
        new Thread(() -> {
            boolean ok = (!l.isEmpty() && isStellio(l, 4000)) || (!r.isEmpty() && isStellio(r, 6000));
            ui.post(() -> {
                connectBtn.setEnabled(true);
                if (ok) { saveAddresses(l, r); showWeb(); reach(true); }
                else { setupStatus.setTextColor(Color.parseColor("#E85D75")); setupStatus.setText(R.string.not_stellio); }
            });
        }).start();
    }

    private void scanQr() {
        try {
            GmsBarcodeScannerOptions opts = new GmsBarcodeScannerOptions.Builder().setBarcodeFormats(Barcode.FORMAT_QR_CODE).build();
            GmsBarcodeScanning.getClient(this, opts).startScan()
                    .addOnSuccessListener(code -> handleLink(code.getRawValue()))
                    .addOnFailureListener(e -> setupStatus.setText(R.string.not_stellio));
        } catch (Exception e) {
            setupStatus.setText(R.string.not_stellio);
        }
    }

    private static boolean isPrivateHost(String h) {
        if (h == null) return false;
        h = h.toLowerCase(Locale.ROOT);
        if (h.endsWith(".local") || h.equals("localhost") || h.startsWith("10.") || h.startsWith("192.168.")) return true;
        if (h.startsWith("172.")) {
            try { int n = Integer.parseInt(h.split("\\.")[1]); return n >= 16 && n <= 31; } catch (Exception e) { return false; }
        }
        return false;
    }

    /** stellio://connect?local=…&remote=… (QR de liaison) ou simple adresse http(s). Retourne true si le lien a été utilisé. */
    private boolean handleLink(String raw) {
        if (raw == null || raw.isEmpty()) return false;
        String l = "", r = "";
        try {
            Uri u = Uri.parse(raw.trim());
            if ("stellio".equals(u.getScheme()) && "connect".equals(u.getHost())) {
                l = normalize(u.getQueryParameter("local")) == null ? "" : normalize(u.getQueryParameter("local"));
                r = normalize(u.getQueryParameter("remote")) == null ? "" : normalize(u.getQueryParameter("remote"));
                if (l.isEmpty()) l = local;      // le QR ne contient pas toujours l'adresse externe : on garde celle déjà enregistrée
                if (r.isEmpty()) r = remote;
            } else if ("http".equals(u.getScheme()) || "https".equals(u.getScheme())) {
                String n = normalize(raw);
                if (n == null) return false;
                if (isPrivateHost(u.getHost())) { l = n; r = remote; } else { r = n; l = local; }
            } else {
                return false;
            }
        } catch (Exception e) {
            return false;
        }
        if (l.isEmpty() && r.isEmpty()) return false;
        saveAddresses(l, r);
        Toast.makeText(this, R.string.paired, Toast.LENGTH_SHORT).show();
        showWeb();
        reach(true);
        ui.removeCallbacks(monitorTask);
        ui.postDelayed(monitorTask, MONITOR_MS);
        return true;
    }

    // ── Réseau, retour, fichiers ──
    private void registerNetworkMonitor() {
        try {
            ConnectivityManager cm = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
            netCallback = new ConnectivityManager.NetworkCallback() {
                private void changed() { ui.removeCallbacks(netTask); ui.postDelayed(netTask, 1500); }
                @Override public void onAvailable(Network n) { changed(); }
                @Override public void onLost(Network n) { changed(); }
                @Override public void onCapabilitiesChanged(Network n, NetworkCapabilities c) { changed(); }
            };
            cm.registerDefaultNetworkCallback(netCallback);
        } catch (Exception ignored) { }
    }

    // ── Photos : appareil photo ou galerie ──
    private boolean hasCamera() { return checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED; }

    private static boolean acceptsImage(WebChromeClient.FileChooserParams p) {
        if (p == null) return false;
        String[] types = p.getAcceptTypes();
        if (types == null) return false;
        for (String t : types) if (t != null && t.toLowerCase(Locale.ROOT).startsWith("image")) return true;
        return false;
    }

    private Uri newPhotoUri() {
        ContentValues v = new ContentValues();
        v.put(MediaStore.Images.Media.DISPLAY_NAME, "stellio_" + new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.ROOT).format(new Date()) + ".jpg");
        v.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
        v.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/Stellio");
        return getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
    }

    private void dropPhoto(Uri u) { try { if (u != null) getContentResolver().delete(u, null, null); } catch (Exception ignored) { } }

    /** Champ « capture » → appareil photo direct ; champ image sans capture → choix galerie / appareil photo ; sinon sélecteur de fichiers. */
    private boolean launchChooser() {
        WebChromeClient.FileChooserParams p = pendingParams;
        try {
            Intent send = p.createIntent();
            if (acceptsImage(p) && hasCamera()) {
                cameraUri = newPhotoUri();
                if (cameraUri != null) {
                    Intent shot = new Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                            .putExtra(MediaStore.EXTRA_OUTPUT, cameraUri)
                            .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    if (p.isCaptureEnabled()) send = shot;
                    else { send = Intent.createChooser(send, null); send.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{shot}); }
                }
            }
            startActivityForResult(send, REQ_FILE);
            return true;
        } catch (Exception e) {
            dropPhoto(cameraUri); cameraUri = null;
            if (filePathCallback != null) filePathCallback.onReceiveValue(null);
            filePathCallback = null;
            return false;
        }
    }

    @Override
    public void onRequestPermissionsResult(int req, String[] perms, int[] results) {
        super.onRequestPermissionsResult(req, perms, results);
        if (req == REQ_CAM_FILE && filePathCallback != null) launchChooser();
        if (req == REQ_CAM_WEB && pendingWebPerm != null) {
            if (hasCamera()) pendingWebPerm.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE}); else pendingWebPerm.deny();
            pendingWebPerm = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (visible(setupView) && !(local.isEmpty() && remote.isEmpty())) { showWeb(); reach(true); return; }
        if (visible(web) && web.canGoBack()) { web.goBack(); return; }
        long now = System.currentTimeMillis();
        if (now - lastBack < 2000) { super.onBackPressed(); return; }
        lastBack = now;
        Toast.makeText(this, R.string.press_again, Toast.LENGTH_SHORT).show();
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        if (req == REQ_FILE && filePathCallback != null) {
            Uri[] result = null;
            if (res == RESULT_OK) {
                result = WebChromeClient.FileChooserParams.parseResult(res, data);
                if (result == null && cameraUri != null) result = new Uri[]{cameraUri};          // photo prise
                else if (cameraUri != null) dropPhoto(cameraUri);                                 // fichier choisi : photo inutile
            } else {
                dropPhoto(cameraUri);
            }
            cameraUri = null;
            filePathCallback.onReceiveValue(result);
            filePathCallback = null;
            return;
        }
        super.onActivityResult(req, res, data);
    }

    @Override protected void onResume() { super.onResume(); web.onResume(); ui.removeCallbacks(netTask); ui.postDelayed(netTask, 500); }
    @Override protected void onPause() { web.onPause(); CookieManager.getInstance().flush(); super.onPause(); }

    @Override
    protected void onDestroy() {
        ui.removeCallbacksAndMessages(null);
        try { if (netCallback != null) ((ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE)).unregisterNetworkCallback(netCallback); } catch (Exception ignored) { }
        web.destroy();
        super.onDestroy();
    }
}
