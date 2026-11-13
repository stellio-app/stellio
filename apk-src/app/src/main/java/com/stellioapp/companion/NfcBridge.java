package com.stellioapp.companion;

import android.app.Activity;
import android.nfc.NdefMessage;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.nfc.tech.NdefFormatable;
import android.os.Handler;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

/**
 * Pont NFC pour les étiquettes OpenPrintTag (NFC-V / ICODE SLIX2, type MIME application/vnd.openprinttag).
 * Le serveur Stellio fait tout le codage : l'application ne lit et n'écrit que le message NDEF brut.
 *
 * Côté page web : window.StellioAndroid.nfcRead() / nfcWrite(ndefBase64) ; le résultat revient par
 * window.__stellioNfcResult(json) avec {ok, payload_b64, uid, capacity, error}.
 */
public class NfcBridge implements NfcAdapter.ReaderCallback {
    private final Activity act;
    private final WebView web;
    private final Handler ui;
    private final NfcAdapter adapter;
    private volatile String mode = "";          // "read" | "write" | ""
    private volatile byte[] pending;

    public NfcBridge(Activity act, WebView web, Handler ui) {
        this.act = act;
        this.web = web;
        this.ui = ui;
        this.adapter = NfcAdapter.getDefaultAdapter(act);
    }

    @JavascriptInterface
    public boolean nfcSupported() { return adapter != null && adapter.isEnabled(); }

    @JavascriptInterface
    public void nfcRead(String ignored) { start("read", null); }

    @JavascriptInterface
    public void nfcWrite(String ndefB64) {
        try { start("write", Base64.decode(ndefB64, Base64.DEFAULT)); } catch (Exception e) { fail("bad_data"); }
    }

    private void start(String m, byte[] data) {
        if (adapter == null || !adapter.isEnabled()) { fail("nfc_off"); return; }
        mode = m;
        pending = data;
        ui.post(() -> {
            try {
                adapter.enableReaderMode(act, this,
                        NfcAdapter.FLAG_READER_NFC_V | NfcAdapter.FLAG_READER_NO_PLATFORM_SOUNDS, null);
            } catch (Exception e) { fail("nfc_error"); }
        });
    }

    /** Arrête l'écoute (appelé quand l'application passe en arrière-plan). */
    public void stop() {
        mode = "";
        pending = null;
        try { if (adapter != null) adapter.disableReaderMode(act); } catch (Exception ignored) { }
    }

    @Override
    public void onTagDiscovered(Tag tag) {
        final String m = mode;
        if (m.isEmpty()) return;
        try {
            Ndef ndef = Ndef.get(tag);
            JSONObject out = new JSONObject();
            out.put("uid", hex(tag.getId()));
            if ("read".equals(m)) {
                if (ndef == null) { fail("no_ndef"); return; }
                ndef.connect();
                try {
                    NdefMessage msg = ndef.getNdefMessage();
                    if (msg == null) { fail("empty"); return; }
                    out.put("ok", true);
                    out.put("payload_b64", Base64.encodeToString(msg.toByteArray(), Base64.NO_WRAP));
                    out.put("capacity", ndef.getMaxSize());
                } finally { ndef.close(); }
            } else {
                byte[] data = pending;
                if (data == null) { fail("bad_data"); return; }
                NdefMessage msg = new NdefMessage(data);
                if (ndef != null) {
                    ndef.connect();
                    try {
                        if (!ndef.isWritable()) { fail("read_only"); return; }
                        if (msg.toByteArray().length > ndef.getMaxSize()) { fail("too_big"); return; }
                        ndef.writeNdefMessage(msg);
                    } finally { ndef.close(); }
                    out.put("capacity", ndef.getMaxSize());
                } else {
                    NdefFormatable f = NdefFormatable.get(tag);     // étiquette vierge : on la formate avec le message
                    if (f == null) { fail("no_ndef"); return; }
                    f.connect();
                    try { f.format(msg); } finally { f.close(); }
                }
                out.put("ok", true);
            }
            stop();
            deliver(out.toString());
        } catch (Exception e) {
            fail("io_error");
        }
    }

    private void fail(String code) {
        stop();
        try { deliver(new JSONObject().put("ok", false).put("error", code).toString()); } catch (Exception ignored) { }
    }

    private void deliver(String json) {
        final String js = "window.__stellioNfcResult&&window.__stellioNfcResult(" + JSONObject.quote(json) + ")";
        ui.post(() -> web.evaluateJavascript(js, null));
    }

    private static String hex(byte[] b) {
        StringBuilder sb = new StringBuilder();
        for (byte x : b) sb.append(String.format("%02x", x));
        return sb.toString();
    }
}
