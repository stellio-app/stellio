"""Stellio — export comptable mensuel (ZIP : CSV des documents, PDF des factures, récapitulatif des totaux)

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `accounting_zip.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.

Complète l'export CSV existant (`/api/quotes/export.csv`) : un seul fichier ZIP par période, prêt à remettre au comptable.
Contenu : `documents.csv` (même format que l'export CSV), `recapitulatif.csv` (totaux par type et par mois),
`pdf/<type>/<numéro>.pdf` (factures, factures d'acompte, avoirs ; devis si demandé) et `LISEZMOI.txt`.
"""
import csv
import datetime
import io
import re
import zipfile
from pathlib import Path

_REQUIRED = (
    '_csv_args',
    '_ensure_quote_columns',
    '_iso_date',
    '_quote_eff_status',
    '_quotes_csv_bytes',
    '_stored_quote_path',
    '_wv_save_dialog',
    'Response',
    'app',
    'app_logger',
    'get_db',
    'jsonify',
    'login_required',
    'request',
    'session',
)
_OVERRIDABLE = ('csv', 'datetime', 'io', 'os', 'zipfile', 'Path')

_MAIN = {}
_csv_args = None
_ensure_quote_columns = None
_iso_date = None
_quote_eff_status = None
_quotes_csv_bytes = None
_stored_quote_path = None
_wv_save_dialog = None
Response = None
app = None
app_logger = None
get_db = None
jsonify = None
login_required = None
request = None
session = None

_TYPE_LABELS = {
    'fr': {'quote': 'Devis', 'invoice': 'Facture', 'deposit': "Facture d'acompte", 'credit': 'Avoir'},
    'en': {'quote': 'Quote', 'invoice': 'Invoice', 'deposit': 'Deposit invoice', 'credit': 'Credit note'},
}
_RECAP_HEAD = {
    'fr': ['Période', 'Type', 'Nombre', 'Total', 'Dont payé', 'Reste à encaisser'],
    'en': ['Period', 'Type', 'Count', 'Total', 'Of which paid', 'Outstanding'],
}


def _period_args(src):
    """`month=AAAA-MM` est un raccourci pour `from` / `to` ; sinon `from` / `to` comme l'export CSV."""
    f, t, types, lang = _csv_args(src)
    month = str(src.get('month') or '').strip()
    if re.match(r'^\d{4}-(0[1-9]|1[0-2])$', month):
        y, m = int(month[:4]), int(month[5:7])
        last = (datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).day
        f, t = f"{month}-01", f"{month}-{last:02d}"
    include_quotes = str(src.get('include_quotes') or '') in ('1', 'true', 'True')
    return f, t, types, lang, include_quotes


def _safe_name(s):
    s = re.sub(r'[^\w\-. ]', '_', str(s or ''), flags=re.U).strip(' ._')
    return (s or 'document')[:80]


def _fmt(v, dec):
    return f"{float(v or 0):.2f}".replace('.', dec)


def _recap_rows(rows, lg):
    """Totaux par mois et par type ; les avoirs sont négatifs, donc déjà déduits du net."""
    dec = ',' if lg == 'fr' else '.'
    agg = {}
    for r in rows:
        dt = r['doc_type'] or 'quote'
        if dt == 'quote':
            continue
        month = str(r['created_at'] or '')[:7]
        a = agg.setdefault((month, dt), {'n': 0, 'total': 0.0, 'paid': 0.0})
        tv = float(r['total_value'] or 0)
        a['n'] += 1
        a['total'] += tv
        if (r['status'] or '') == 'paid':
            a['paid'] += tv
    out = []
    net = {}
    for (month, dt) in sorted(agg):
        a = agg[(month, dt)]
        rest = a['total'] - a['paid'] if dt in ('invoice', 'deposit') else 0.0
        out.append([month, _TYPE_LABELS[lg][dt], a['n'], _fmt(a['total'], dec), _fmt(a['paid'], dec), _fmt(rest, dec)])
        net[month] = net.get(month, 0.0) + a['total']
    for month in sorted(net):
        out.append([month, 'NET' if lg == 'en' else 'NET (avoirs déduits)', '', _fmt(net[month], dec), '', ''])
    return out


def build_zip(user_id, date_from, date_to, types, lang, include_quotes=False):
    """Retourne (octets du ZIP, nombre de documents)."""
    lg = 'fr' if lang == 'fr' else 'en'
    _ensure_quote_columns()
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM quotes WHERE user_id = ? ORDER BY created_at, id", (user_id,)).fetchall()
    finally:
        conn.close()
    picked = []
    for r in rows:
        dt = r['doc_type'] or 'quote'
        day = str(r['created_at'] or '')[:10]
        if types and dt not in types:
            continue
        if (date_from and day < date_from) or (date_to and day > date_to):
            continue
        picked.append(r)
    buf = io.BytesIO()
    used = set()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('documents.csv', _quotes_csv_bytes(user_id, date_from, date_to, types, lang))
        recap = io.StringIO()
        w = csv.writer(recap, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        w.writerow(_RECAP_HEAD[lg])
        for line in _recap_rows(picked, lg):
            w.writerow(line)
        z.writestr('recapitulatif.csv', ('﻿' + recap.getvalue()).encode('utf-8'))
        for r in picked:
            dt = r['doc_type'] or 'quote'
            if dt == 'quote' and not include_quotes:
                continue
            path = _stored_quote_path(r)
            if not path:
                continue
            base = f"pdf/{dt}/{_safe_name(r['number'])}"
            name, k = f"{base}.pdf", 2
            while name in used:
                name, k = f"{base}-{k}.pdf", k + 1
            used.add(name)
            z.write(path, name)
        period = f"{date_from or '…'} → {date_to or '…'}"
        readme = (f"Export comptable Stellio — {datetime.date.today().isoformat()}\nPériode : {period}\n"
                  f"Documents : {len(picked)}\n\ndocuments.csv : liste des documents (séparateur « ; », UTF-8).\n"
                  "recapitulatif.csv : totaux par mois et par type (les avoirs sont négatifs).\n"
                  "pdf/ : copies des documents émis.\n") if lg == 'fr' else (
            f"Stellio accounting export — {datetime.date.today().isoformat()}\nPeriod: {period}\n"
            f"Documents: {len(picked)}\n\ndocuments.csv: document list (\";\" separator, UTF-8).\n"
            "recapitulatif.csv: totals per month and type (credit notes are negative).\npdf/: copies of the issued documents.\n")
        z.writestr('LISEZMOI.txt', readme)
    return buf.getvalue(), len(picked)


def _zip_filename(date_from, date_to):
    tag = (date_from[:7] if date_from and date_from[:7] == (date_to or '')[:7] else
           f"{date_from or 'debut'}_{date_to or 'fin'}")
    return f"stellio-comptabilite-{tag}.zip"


def api_quotes_export_zip():
    f, t, types, lang, inc = _period_args(request.args)
    data, n = build_zip(session['user_id'], f, t, types, lang, inc)
    return Response(data, mimetype='application/zip', headers={
        'Content-Disposition': f'attachment; filename="{_zip_filename(f, t)}"', 'X-Stellio-Documents': str(n)})


def api_quotes_export_zip_native():
    """Variante pour l'application de bureau : boîte « Enregistrer sous » native (le téléchargement du navigateur intégré est limité)."""
    f, t, types, lang, inc = _period_args(request.get_json(silent=True) or {})
    data, n = build_zip(session['user_id'], f, t, types, lang, inc)
    try:
        import webview
        result = webview.windows[0].create_file_dialog(
            _wv_save_dialog(webview), directory=str(Path.home() / 'Documents'),
            save_filename=_zip_filename(f, t), file_types=('Archive ZIP (*.zip)',))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    dest = result[0] if isinstance(result, (list, tuple)) and result else result
    if not dest:
        return jsonify({'success': False, 'cancelled': True}), 200
    dest = str(dest)
    if not dest.lower().endswith('.zip'):
        dest += '.zip'
    try:
        with open(dest, 'wb') as fh:
            fh.write(data)
        return jsonify({'success': True, 'path': dest, 'documents': n})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


_ROUTES = (
    ('/api/quotes/export-zip', ['GET'], 'api_quotes_export_zip', ('login_required', )),
    ('/api/quotes/export-zip-native', ['POST'], 'api_quotes_export_zip_native', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"accounting_zip.init : services manquants : {missing}")
    for n in _REQUIRED + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {}
