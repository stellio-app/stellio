"""Stellio — devis

Module séparé de main.py (même schéma que print_session.py) : main.py appelle `pro_quotes.init(globals())` une fois
toutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.
Généré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.
"""
from pathlib import Path
import base64
import datetime
import io
import json
import os
import re
import secrets
import shutil
import sqlite3
import ssl

_REQUIRED = (
    'DATA_DIR',
    'Image',
    'Response',
    '_ensure_optional_module',
    '_unicodedata',
    '_wv_save_dialog',
    'app',
    'app_logger',
    'get_db',
    'importlib',
    'jsonify',
    'load_settings',
    'login_required',
    'request',
    'save_settings',
    'send_file',
    'session',
    'trash_record',
)
_OPTIONAL = ('webview', )   # fournis seulement s'ils existent dans main.py (import facultatif)
_OVERRIDABLE = ('Path', 'base64', 'datetime', 'io', 'json', 'os', 're', 'secrets', 'shutil', 'sqlite3', 'ssl', )

_EXPORTS = ('_client_clean', '_ensure_quote_columns', '_quote_eff_status', '_quote_payload_path', '_stored_quote', '_stored_quote_path', '_build_quote_pdf_with_repair', '_csv_args', '_iso_date', '_int_or0', '_quotes_csv_bytes', 'QUOTES_DIR', 'QUOTE_LOGO_FILE')   # services rendus au cœur et aux autres modules du plugin (via le dict renvoyé par init)

_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')
webview = None
# Valeurs réelles posées par init() (None tant que le module n'est pas branché).
DATA_DIR = None
Image = None
Response = None
_ensure_optional_module = None
_unicodedata = None
_wv_save_dialog = None
app = None
app_logger = None
get_db = None
importlib = None
jsonify = None
load_settings = None
login_required = None
request = None
save_settings = None
send_file = None
session = None
trash_record = None


QUOTE_LOGO_FILE = None
QUOTES_DIR = None
def _quote_logo_image(data_url):
    try:
        if not isinstance(data_url, str) or not data_url.startswith('data:image/') or ',' not in data_url:
            return None
        raw = base64.b64decode(data_url.split(',', 1)[1])
        if not raw or len(raw) > 1_500_000:
            return None
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        img.load()
        img = img.convert('RGBA')
        out = io.BytesIO()
        img.save(out, format='PNG')
        out.seek(0)
        return out, img.width, img.height
    except Exception as e:
        app_logger.warning(f"[QUOTE] Logo ignoré (illisible) : {e}")
        return None

def _save_quote_logo_png(png_buf):
    tmp = QUOTE_LOGO_FILE + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(png_buf.getvalue())
    os.replace(tmp, QUOTE_LOGO_FILE)

def _migrate_legacy_quote_logo():
    try:
        settings = load_settings() or {}
        prev = settings.get('_previous_settings')
        has_main = 'quote_logo' in settings
        has_prev = isinstance(prev, dict) and 'quote_logo' in prev
        if not (has_main or has_prev):
            return
        legacy = settings.get('quote_logo') or (prev.get('quote_logo') if has_prev else None)
        if legacy and not os.path.isfile(QUOTE_LOGO_FILE):
            img = _quote_logo_image(legacy)
            if img:
                _save_quote_logo_png(img[0])
        settings.pop('quote_logo', None)
        if has_prev:
            prev.pop('quote_logo', None)
        save_settings(settings)
    except Exception as e:
        app_logger.warning(f"[QUOTE] Migration du logo impossible : {e}")

def _load_quote_logo():
    _migrate_legacy_quote_logo()
    try:
        if os.path.isfile(QUOTE_LOGO_FILE):
            from PIL import Image
            with open(QUOTE_LOGO_FILE, 'rb') as f:
                raw = f.read()
            img = Image.open(io.BytesIO(raw))
            img.load()
            return io.BytesIO(raw), img.width, img.height
    except Exception as e:
        app_logger.warning(f"[QUOTE] Logo illisible : {e}")
    return None

def api_quote_logo_get():
    _migrate_legacy_quote_logo()
    if not os.path.isfile(QUOTE_LOGO_FILE):
        return jsonify({"error": "Aucun logo"}), 404
    resp = send_file(QUOTE_LOGO_FILE, mimetype='image/png', conditional=False)
    resp.headers['Cache-Control'] = 'no-store'
    return resp

def api_quote_logo_set():
    data = request.get_json(silent=True) or {}
    img = _quote_logo_image(data.get('data_url'))
    if not img:
        return jsonify({"error": "Logo invalide ou trop volumineux"}), 400
    try:
        _save_quote_logo_png(img[0])
    except Exception as e:
        app_logger.error(f"[QUOTE] Écriture du logo impossible : {e}")
        return jsonify({"error": "Impossible d'enregistrer le logo"}), 500
    return jsonify({"success": True}), 200

def api_quote_logo_delete():
    try:
        if os.path.isfile(QUOTE_LOGO_FILE):
            os.remove(QUOTE_LOGO_FILE)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    _migrate_legacy_quote_logo()  
    return jsonify({"success": True}), 200

def _quote_pdf_encryption(allow_annotate=False):
    try:
        from reportlab.lib.pdfencrypt import StandardEncryption
        from reportlab.pdfgen import canvas as _rl_canvas
    except Exception as e:
        app_logger.warning(f"[QUOTE] Chiffrement PDF indisponible : {e}")
        return None

    class _LockedEncryption(StandardEncryption):
        def permissionBits(self):
            return super().permissionBits() & ~(1024 | (0 if allow_annotate else 256))

    def make(strength):
        return _LockedEncryption('', ownerPassword=secrets.token_hex(16), canPrint=1, canModify=0,
                                 canCopy=0, canAnnotate=1 if allow_annotate else 0, strength=strength)

    strengths = (256, 128) if importlib.util.find_spec('pyaes') else (128,)
    for strength in strengths:
        try:
            probe = _rl_canvas.Canvas(io.BytesIO(), encrypt=make(strength))
            probe.drawString(10, 10, 'x')
            probe.save()
            return make(strength)
        except Exception as e:
            app_logger.warning(f"[QUOTE] Chiffrement PDF {strength} bits indisponible : {e}")
    return None

def build_quote_pdf_bytes(data, encrypt=True):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from xml.sax.saxutils import escape

    def s(key, limit=200):
        return str(data.get(key) or '')[:limit]

    def p_text(value, limit=200):
        return escape(str(value or '')[:limit]).replace('\n', '<br/>')

    try:
        settings = load_settings() or {}
    except Exception:
        settings = {}

    def cfg(key, limit):
        return str(settings.get(key) or '')[:limit].strip()

    company = cfg('quote_company', 120) or cfg('print_cost_quote_company', 120)
    address = cfg('quote_address', 300)
    phone = cfg('quote_phone', 40)
    email = cfg('quote_email', 120)
    website = cfg('quote_website', 120)
    tax_id = cfg('quote_tax_id', 80)
    legal = cfg('quote_legal', 1500)
    logo = _load_quote_logo()

    lang = s('lang', 8).lower()
    if lang.startswith('ja'):
        font = bold = 'HeiseiKakuGo-W5'
    elif lang.startswith('zh'):
        font = bold = 'STSong-Light'
    else:
        font, bold = 'Helvetica', 'Helvetica-Bold'
    if font != 'Helvetica':
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(font))
        except Exception:
            font, bold = 'Helvetica', 'Helvetica-Bold'

    ink = colors.HexColor('#1a1d2e')
    grey = colors.HexColor('#666666')
    line = colors.HexColor('#dddddd')

    st_title = ParagraphStyle('t', fontName=bold, fontSize=24, leading=28, textColor=ink, alignment=2, spaceAfter=2)
    st_meta = ParagraphStyle('m', fontName=font, fontSize=10, leading=14, textColor=grey, alignment=2)
    st_company = ParagraphStyle('c', fontName=bold, fontSize=13, leading=17, textColor=ink, spaceBefore=4)
    st_issuer = ParagraphStyle('i', fontName=font, fontSize=9, leading=13, textColor=colors.HexColor('#444444'))
    st_label = ParagraphStyle('l', fontName=font, fontSize=8, leading=11, textColor=grey)
    st_body = ParagraphStyle('b', fontName=font, fontSize=10, leading=14, textColor=ink)
    st_sub = ParagraphStyle('s', fontName=font, fontSize=8.5, leading=12, textColor=grey)
    st_th = ParagraphStyle('th', fontName=bold, fontSize=8.5, leading=11, textColor=ink)
    st_th_r = ParagraphStyle('thr', parent=st_th, alignment=2)
    st_num = ParagraphStyle('n', parent=st_body, alignment=2)
    st_total = ParagraphStyle('tot', fontName=bold, fontSize=14, leading=18, textColor=ink, alignment=2, spaceBefore=6)
    st_notes = ParagraphStyle('nt', fontName=font, fontSize=9, leading=13, textColor=colors.HexColor('#444444'))
    st_legal = ParagraphStyle('lg', fontName=font, fontSize=7.5, leading=10, textColor=grey)

    width = A4[0] - 40 * mm

    legal_para = Paragraph(p_text(legal, 1500), st_legal) if legal else None
    bottom_margin = 20 * mm
    if legal_para is not None:
        _, legal_h = legal_para.wrap(width, 250 * mm)
        bottom_margin = max(20 * mm, legal_h + 18 * mm)

    def draw_footer(canvas, _doc):
        if legal_para is None:
            return
        canvas.saveState()
        _, h = legal_para.wrap(width, 250 * mm)
        legal_para.drawOn(canvas, 20 * mm, 10 * mm)
        canvas.setStrokeColor(line)
        canvas.setLineWidth(0.5)
        canvas.line(20 * mm, 10 * mm + h + 3 * mm, 20 * mm + width, 10 * mm + h + 3 * mm)
        canvas.restoreState()

    buf = io.BytesIO()
    top_margin = 18 * mm
    doc = BaseDocTemplate(
        buf, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=top_margin, bottomMargin=bottom_margin,
        title=f"{s('title', 80)} {s('number', 40)}".strip(), author=company or 'Stellio',
        encrypt=_quote_pdf_encryption(allow_annotate=bool(s('signature_label', 60))) if encrypt else None
    )
    frame = Frame(20 * mm, bottom_margin, width, A4[1] - top_margin - bottom_margin,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id='quote')
    doc.addPageTemplates([PageTemplate(id='quote', frames=[frame], onPage=draw_footer)])

    left = []
    if logo is not None:
        buf_logo, lw, lh = logo
        scale = min((50 * mm) / lw, (24 * mm) / lh, 1.0)
        img = RLImage(buf_logo, width=lw * scale, height=lh * scale, mask='auto')
        img.hAlign = 'LEFT'
        left.append(img)
    if company:
        left.append(Paragraph(p_text(company, 120), st_company))
    if address:
        left.append(Paragraph(p_text(address, 300), st_issuer))
    contact = [c for c in (phone, email, website) if c]
    if contact:
        left.append(Paragraph('<br/>'.join(p_text(c, 120) for c in contact), st_issuer))
    if tax_id:
        label = s('tax_id_label', 40)
        left.append(Paragraph((f"{p_text(label)} : " if label else '') + p_text(tax_id, 80), st_issuer))
    if not left:
        left = [Spacer(1, 1)]

    right = [
        Paragraph(p_text(s('title', 80)), st_title),
        Paragraph(f"{p_text(s('number_label', 40))} {p_text(s('number', 40))}", st_meta),
        Paragraph(p_text(s('date', 60)), st_meta),
    ]
    if s('due_date', 60):
        right.append(Paragraph(f"{p_text(s('due_label', 40))} {p_text(s('due_date', 60))}", st_meta))
    if s('ref_value', 60):
        right.append(Paragraph(f"{p_text(s('ref_label', 40))} {p_text(s('ref_value', 60))}", st_meta))
    header = Table([[left, right]], colWidths=[width * 0.58, width * 0.42])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, line), ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
    ]))
    flow = [header, Spacer(1, 16)]

    dash = '&mdash;'
    client_box = Table([
        [Paragraph(p_text(s('to_label', 40)).upper(), st_label)],
        [Paragraph(p_text(s('client', 120)) or dash, st_body)],
    ] + ([[Paragraph('<br/>'.join(p_text(x, 120) for x in str(data.get('client_details') or '').splitlines()[:6] if x.strip()), st_issuer)]]
         if str(data.get('client_details') or '').strip() else []), colWidths=[width * 0.5])
    client_box.hAlign = 'LEFT'
    client_box.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
    ]))
    flow += [client_box, Spacer(1, 18)]

    desc_cell = [Paragraph(p_text(s('item_desc', 200)), st_body), Paragraph(p_text(s('item_details', 200)), st_sub)]

    # Miniatures des objets (optionnelles) : images JPEG/PNG envoyées par l'interface en data-URL
    thumbs = []
    raw_thumbs = data.get('thumbnails')
    if isinstance(raw_thumbs, list):
        import base64 as _b64
        for item in raw_thumbs[:12]:
            try:
                head, _, b64 = str(item).partition(',')
                if not head.startswith('data:image/') or len(b64) > 700000:
                    continue
                im = Image.open(io.BytesIO(_b64.b64decode(b64)))
                im.load()
                im = im.convert('RGB')
                im.thumbnail((320, 320))
                tb = io.BytesIO()
                im.save(tb, 'JPEG', quality=88)
                tb.seek(0)
                thumbs.append((tb, im.size))
            except Exception as thumb_err:
                app_logger.info(f"[QUOTE] Miniature ignorée : {thumb_err}")
    if thumbs:
        cell_w = width * 0.48 - 8
        per_row = 3 if len(thumbs) > 1 else 1
        box = min(24 * mm, (cell_w - 4 * mm * (per_row - 1)) / per_row) if per_row > 1 else 34 * mm
        rows, cur_row = [], []
        for tb, (iw, ih) in thumbs:
            sc = min(box / iw, box / ih)
            cur_row.append(RLImage(tb, width=iw * sc, height=ih * sc))
            if len(cur_row) == per_row:
                rows.append(cur_row)
                cur_row = []
        if cur_row:
            rows.append(cur_row + [''] * (per_row - len(cur_row)))
        thumb_tbl = Table(rows, colWidths=[box + 4 * mm] * per_row)
        thumb_tbl.hAlign = 'LEFT'
        thumb_tbl.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 4 * mm),
            ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        desc_cell += [Spacer(1, 4), thumb_tbl]
    items = Table([
        [Paragraph(p_text(s('description_label', 40)).upper(), st_th), Paragraph(p_text(s('qty_label', 20)).upper(), st_th_r),
         Paragraph(p_text(s('unit_label', 40)).upper(), st_th_r), Paragraph(p_text(s('line_total_label', 40)).upper(), st_th_r)],
        [desc_cell, Paragraph(p_text(s('qty', 12)), st_num), Paragraph(p_text(s('unit_price', 30)), st_num),
         Paragraph(p_text(s('line_total', 30)), st_num)],
    ], colWidths=[width * 0.48, width * 0.10, width * 0.21, width * 0.21])
    items.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, ink),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, line),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    flow += [items]
    if s('discount', 30):
        st_sum_l = ParagraphStyle('sl', parent=st_body, alignment=2, textColor=grey)
        sums = Table([[Paragraph(p_text(s('subtotal_label', 40)), st_sum_l), Paragraph(p_text(s('line_total', 30)), st_num)],
                      [Paragraph(p_text(s('discount_label', 60)), st_sum_l), Paragraph(p_text(s('discount', 30)), st_num)]],
                     colWidths=[width * 0.62, width * 0.38])
        sums.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                                  ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        flow += [Spacer(1, 6), sums]
    if s('deposit', 30):
        st_sum_l2 = ParagraphStyle('sl2', parent=st_body, alignment=2, textColor=grey)
        sums2 = Table([[Paragraph(p_text(s('total_label', 40)), st_sum_l2), Paragraph(p_text(s('grand_total', 30) or s('line_total', 30)), st_num)],
                       [Paragraph(p_text(s('deposit_label', 60)), st_sum_l2), Paragraph(p_text(s('deposit', 30)), st_num)]],
                      colWidths=[width * 0.62, width * 0.38])
        sums2.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                                   ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
        flow += [Spacer(1, 6), sums2,
                 Paragraph(f"{p_text(s('net_label', 40))} : {p_text(s('net_total', 30))}", st_total)]
    else:
        flow += [Paragraph(f"{p_text(s('total_label', 40))} : {p_text(s('grand_total', 30) or s('line_total', 30))}", st_total)]

    payment = s('payment_terms', 300).strip()
    if payment:
        pay_box = Table([[Paragraph(f"<b>{p_text(s('payment_label', 60))}</b><br/>{p_text(payment, 300)}", st_notes)]], colWidths=[width])
        pay_box.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), 0.5, line), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                     ('TOPPADDING', (0, 0), (-1, -1), 10)]))
        flow += [Spacer(1, 18), pay_box]

    notes = s('notes', 500).strip()
    if notes:
        notes_box = Table([[Paragraph(p_text(notes, 500), st_notes)]], colWidths=[width])
        notes_box.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, line), ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        flow += [Spacer(1, 22), notes_box]

    sign_label = s('signature_label', 60).strip()
    if sign_label:
        from reportlab.platypus import KeepTogether
        from reportlab.pdfbase import pdfmetrics
        from reportlab.platypus.flowables import Flowable

        class _CheckBox(Flowable):
            def __init__(self, size=11):
                Flowable.__init__(self); self.size = size; self.width = size; self.height = size
            def draw(self):
                self.canv.setLineWidth(0.8); self.canv.setStrokeColor(colors.HexColor('#333333'))
                self.canv.rect(0, 0, self.size, self.size, stroke=1, fill=0)
                try:  # case réellement cochable à l'écran
                    ax, ay = self.canv.absolutePosition(0, 0)
                    self.canv.acroForm.checkbox(name='approved', x=ax, y=ay, size=self.size, borderWidth=0, borderColor=None,
                                                fillColor=None, textColor=colors.HexColor('#222222'), forceBorder=False, checked=False)
                except Exception:
                    pass


        class _DateFields(Flowable):
            """« Date : ../../.... » : seuls les points sont modifiables (champs de formulaire), le reste est figé."""
            def __init__(self, label, fnt):
                Flowable.__init__(self); self.label = label; self.fnt = fnt
                self.width = 60 * mm; self.height = 7 * mm
            def wrap(self, aw, ah):
                return self.width, self.height
            def draw(self):
                c = self.canv
                c.setFont(self.fnt, 9); c.setFillColor(colors.HexColor('#555555'))
                x = pdfmetrics.stringWidth(self.label, self.fnt, 9) + 6
                c.drawString(0, 2, self.label)
                x_cur = x
                for i, (nm, val, w) in enumerate((('date_day', '..', 6 * mm), ('date_month', '..', 6 * mm), ('date_year', '....', 11 * mm))):
                    if i:
                        c.setFont('Helvetica', 9); c.drawString(x_cur, 2, '/'); x_cur += 5
                    try:
                        ax, ay = c.absolutePosition(x_cur, -1.8)
                        # Au clic les points disparaissent (script de focus), et reviennent si le champ reste vide.
                        _orig_add = c._addAnnotation
                        def _add_with_js(ann, _o=_orig_add, _v=val):
                            try:
                                from reportlab.pdfbase.pdfdoc import PDFDictionary, PDFName, PDFString
                                def _act(js):
                                    return PDFDictionary({'S': PDFName('JavaScript'), 'JS': PDFString(js)})
                                ann.dict['AA'] = PDFDictionary({
                                    'Fo': _act("if (event.target.value == '%s') event.target.value = '';" % _v),
                                    'Bl': _act("if (event.target.value == '') event.target.value = '%s';" % _v)})
                            except Exception:
                                pass
                            return _o(ann)
                        c._addAnnotation = _add_with_js
                        c.acroForm.textfield(name=nm, value=val, x=ax, y=ay, width=w, height=4.2 * mm, borderWidth=0,
                                             fillColor=None, borderColor=None, textColor=colors.HexColor('#222222'),
                                             fontName='Helvetica', fontSize=9, maxlen=len(val), forceBorder=False,
                                             fieldFlags='')
                    except Exception:
                        c.setFont('Helvetica', 10); c.drawString(x_cur, 2, val)
                    finally:
                        c._addAnnotation = _orig_add
                    x_cur += w

        st_mention = ParagraphStyle('mn', fontName=font, fontSize=9.5, leading=13, textColor=colors.HexColor('#222222'))
        st_sign_l = ParagraphStyle('sl', fontName=font, fontSize=9, leading=12, textColor=colors.HexColor('#555555'))
        mention = Table([[_CheckBox(), Paragraph(p_text(s('signature_mention', 200)), st_mention)]], colWidths=[9 * mm, width * 0.5 - 9 * mm], hAlign='RIGHT')
        mention.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                     ('TOPPADDING', (0, 0), (-1, -1), 1), ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
        sign_box = Table([[_DateFields(s('signature_date', 30), font)], [Paragraph(p_text(sign_label), st_sign_l)], ['']],
                         colWidths=[width * 0.5], rowHeights=[None, None, 22 * mm], hAlign='RIGHT')
        sign_box.setStyle(TableStyle([('LINEBELOW', (0, 2), (0, 2), 0.5, line), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                      ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
        flow += [Spacer(1, 22), KeepTogether([mention, Spacer(1, 6), sign_box])]

    terms_title = s('terms_title', 80).strip()
    terms = (cfg('quote_terms', 6000) or str(data.get('terms') or '')[:6000]).strip()
    if terms_title and terms:
        from reportlab.platypus import PageBreak
        st_t_title = ParagraphStyle('tt', fontName=bold, fontSize=15, leading=19, textColor=colors.HexColor('#1a1f2b'), spaceAfter=10)
        st_t_body = ParagraphStyle('tb', fontName=font, fontSize=8.6, leading=11.6, textColor=colors.HexColor('#333333'), spaceAfter=5)
        flow += [PageBreak(), Paragraph(p_text(terms_title, 80), st_t_title)]
        for ln in terms.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            head, sep, rest = ln.partition(' : ') if ' : ' in ln[:80] else ln.partition(': ') if ': ' in ln[:80] else (ln, '', '')
            if sep and len(head) <= 70:
                flow.append(Paragraph(f"<b>{p_text(head, 70)}</b> : {p_text(rest, 1500)}", st_t_body))
            else:
                flow.append(Paragraph(p_text(ln, 1500), st_t_body))

    doc.build(flow)
    return buf.getvalue()

def _build_quote_pdf_with_repair(data, encrypt=True):
    """Génère le devis ; si reportlab manque (version empaquetée mise à jour par patch), tente une réparation puis réessaie."""
    try:
        return build_quote_pdf_bytes(data, encrypt=encrypt)
    except ImportError:
        if _ensure_optional_module('reportlab.platypus', 'reportlab'):
            return build_quote_pdf_bytes(data, encrypt=encrypt)
        raise

def _safe_quote_pdf_filename(name):
    name = os.path.basename(str(name or '')).strip()
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', name)[:120]
    if not name.lower().endswith('.pdf'):
        name = (name or 'stellio-devis') + '.pdf'
    return name

_QUOTE_COLS_DONE = False

def _ensure_quote_columns():
    """Colonnes ajoutées en 0.8.7 : type de document (devis / facture), devis d'origine, remise, charge utile complète."""
    global _QUOTE_COLS_DONE
    if _QUOTE_COLS_DONE:
        return
    conn = get_db()
    try:
        cols = {r['name'] for r in conn.execute("PRAGMA table_info(quotes)").fetchall()}
        for name, ddl in (('doc_type', "TEXT DEFAULT 'quote'"), ('source_quote_id', 'INTEGER DEFAULT 0'),
                          ('discount_value', 'REAL DEFAULT 0'), ('payload_file', "TEXT DEFAULT ''"),
                          ('status', "TEXT DEFAULT ''"), ('due_date', "TEXT DEFAULT ''"), ('paid_at', "TEXT DEFAULT ''"),
                          ('sent_at', "TEXT DEFAULT ''"), ('client_id', 'INTEGER DEFAULT 0')):
            if name not in cols:
                try:
                    conn.execute(f"ALTER TABLE quotes ADD COLUMN {name} {ddl}")
                except sqlite3.OperationalError as e:      # deux requêtes simultanées au premier lancement (course) — la colonne existe alors déjà
                    if 'duplicate column' not in str(e).lower():
                        raise
        conn.execute("""CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL DEFAULT '',
            email TEXT DEFAULT '', phone TEXT DEFAULT '', address TEXT DEFAULT '', tax_id TEXT DEFAULT '',
            notes TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.commit()
    finally:
        conn.close()
    _QUOTE_COLS_DONE = True

def _iso_date(v):
    v = str(v or '').strip()[:10]
    return v if re.match(r'^\d{4}-\d{2}-\d{2}$', v) else ''

def _int_or0(v):
    try:
        return max(0, int(v))
    except (TypeError, ValueError):
        return 0

def _quote_eff_status(row):
    """Statut affiché : brouillon / envoyé / accepté / refusé / payé / en retard (calculé d'après l'échéance)."""
    dt = (row['doc_type'] or 'quote')
    st = (row['status'] or 'draft')
    if dt in ('invoice', 'deposit') and st != 'paid':
        due = row['due_date'] or ''
        if due and due < datetime.date.today().isoformat():
            return 'overdue'
    return st

def _quote_payload_path(row):
    name = os.path.basename((row['payload_file'] if 'payload_file' in row.keys() else '') or '')
    return os.path.join(QUOTES_DIR, name) if name else ''

def _write_quote_files(user_id, qid, data, pdf_bytes):
    os.makedirs(QUOTES_DIR, exist_ok=True)
    pdf_name = f"quote_{user_id}_{qid}.pdf"
    json_name = f"quote_{user_id}_{qid}.json"
    with open(os.path.join(QUOTES_DIR, pdf_name), 'wb') as f_pdf:
        f_pdf.write(pdf_bytes)
    with open(os.path.join(QUOTES_DIR, json_name), 'w', encoding='utf-8') as f_js:
        json.dump(data, f_js, ensure_ascii=False)
    return pdf_name, json_name

def _quote_fields(data):
    def t(key, limit):
        return str(data.get(key) or '')[:limit]
    try:
        total_value = float(data.get('total_value') or 0)
    except (TypeError, ValueError):
        total_value = 0.0
    try:
        discount_value = float(data.get('discount_value') or 0)
    except (TypeError, ValueError):
        discount_value = 0.0
    return (t('number', 40), t('client', 120), t('item_desc', 200), t('item_details', 200), t('qty', 20), t('unit_price', 40),
            t('net_total', 40) or t('grand_total', 40) or t('line_total', 40), total_value, t('notes', 500), discount_value)

def _record_quote(user_id, data, pdf_bytes, doc_type='quote', source_id=0):
    """Enregistre un devis (ou une facture) dans l'historique, avec une copie du PDF et de ses données.
    Ne doit jamais faire échouer l'export. Retourne l'id créé (ou None)."""
    try:
        _ensure_quote_columns()
        number, client, desc, details, qty, unit_price, total, total_value, notes, discount = _quote_fields(data)
        conn = get_db()
        try:
            cur = conn.execute(
                """INSERT INTO quotes (user_id, number, client, item_desc, item_details, qty, unit_price,
                                       total, total_value, notes, filename, doc_type, source_quote_id, discount_value,
                                       status, due_date, client_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)""",
                (user_id, number, client, desc, details, qty, unit_price, total, total_value, notes,
                 _safe_quote_pdf_filename(data.get('filename')), doc_type, int(source_id or 0), discount,
                 _iso_date(data.get('due_iso')), _int_or0(data.get('client_id')))
            )
            qid = cur.lastrowid
            pdf_name, json_name = _write_quote_files(user_id, qid, data, pdf_bytes)
            conn.execute("UPDATE quotes SET pdf_file = ?, payload_file = ? WHERE id = ?", (pdf_name, json_name, qid))
            conn.commit()
            return qid
        finally:
            conn.close()
    except Exception as e:
        app_logger.warning(f"[QUOTE] Historique : enregistrement impossible : {e}")
        return None

def api_quotes_list():
    _ensure_quote_columns()
    try:
        limit = max(1, min(int(request.args.get('limit', 200)), 500))
    except (TypeError, ValueError):
        limit = 200
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT q.id, q.number, q.client, q.item_desc, q.item_details, q.qty, q.unit_price, q.total, q.total_value, q.notes,
                      q.filename, q.created_at, (q.pdf_file != '') AS has_pdf, q.doc_type, q.source_quote_id, q.discount_value,
                      q.status, q.due_date, q.paid_at, q.sent_at, q.client_id,
                      (SELECT i.id FROM quotes i WHERE i.source_quote_id = q.id AND i.doc_type = 'invoice' LIMIT 1) AS invoice_id,
                      (SELECT COUNT(*) FROM quotes d WHERE d.source_quote_id = q.id AND d.doc_type = 'deposit') AS deposit_count,
                      (SELECT COALESCE(SUM(-c.total_value), 0) FROM quotes c WHERE c.source_quote_id = q.id AND c.doc_type = 'credit') AS credited,
                      (SELECT s.number FROM quotes s WHERE s.id = q.source_quote_id) AS source_number
               FROM quotes q WHERE q.user_id = ? ORDER BY q.id DESC LIMIT ?""",
            (session['user_id'], limit)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM quotes WHERE user_id = ?", (session['user_id'],)).fetchone()[0]
    finally:
        conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d['status'] = _quote_eff_status(r)
        out.append(d)
    return jsonify({"quotes": out, "total": total})

def _stored_quote(qid):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM quotes WHERE id = ? AND user_id = ?", (qid, session['user_id'])).fetchone()
    finally:
        conn.close()
    return row

def _stored_quote_path(row):
    name = os.path.basename(row['pdf_file'] or '')
    path = os.path.join(QUOTES_DIR, name) if name else ''
    return path if path and os.path.isfile(path) else None

def api_quote_history_payload(qid):
    """Données complètes d'un devis/facture (pour le modifier ou en tirer une facture)."""
    _ensure_quote_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({"error": "Not found"}), 404
    payload = {}
    path = _quote_payload_path(row)
    if path and os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
        except Exception:
            payload = {}
    conn = get_db()
    try:
        inv = conn.execute("SELECT id, number FROM quotes WHERE source_quote_id = ? AND doc_type = 'invoice' AND user_id = ?",
                           (qid, session['user_id'])).fetchone()
    finally:
        conn.close()
    meta = {k: row[k] for k in ('id', 'number', 'client', 'item_desc', 'item_details', 'qty', 'unit_price', 'total', 'total_value',
                                 'notes', 'created_at', 'doc_type', 'discount_value')}
    meta['invoice'] = dict(inv) if inv else None
    conn = get_db()
    try:
        dep = conn.execute("SELECT COALESCE(SUM(total_value),0) FROM quotes WHERE source_quote_id = ? AND doc_type = 'deposit' AND user_id = ?",
                           (qid, session['user_id'])).fetchone()[0]
        cre = conn.execute("SELECT COALESCE(SUM(-total_value),0) FROM quotes WHERE source_quote_id = ? AND doc_type = 'credit' AND user_id = ?",
                           (qid, session['user_id'])).fetchone()[0]
        cl = conn.execute("SELECT * FROM clients WHERE id = ? AND user_id = ?", (row['client_id'] or 0, session['user_id'])).fetchone()
    finally:
        conn.close()
    meta.update({'status': _quote_eff_status(row), 'due_date': row['due_date'], 'paid_at': row['paid_at'], 'client_id': row['client_id'],
                 'deposits_total': round(dep, 2), 'credited_total': round(cre, 2), 'client_record': dict(cl) if cl else None})
    return jsonify({"row": meta, "payload": payload})

def api_quote_history_update(qid):
    """Modifie un devis déjà généré : le PDF est régénéré et remplace l'ancien (même numéro)."""
    _ensure_quote_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({"success": False, "error": "not_found"}), 404
    if (row['doc_type'] or 'quote') != 'quote':
        return jsonify({"success": False, "error": "not_a_quote"}), 400
    conn = get_db()
    try:
        has_invoice = conn.execute("SELECT 1 FROM quotes WHERE source_quote_id = ? AND doc_type IN ('invoice','deposit')", (qid,)).fetchone()
    finally:
        conn.close()
    if has_invoice:
        return jsonify({"success": False, "error": "invoice_exists"}), 409
    data = request.get_json(silent=True) or {}
    data['number'] = row['number']
    data['filename'] = row['filename']
    try:
        pdf_bytes = _build_quote_pdf_with_repair(data)
    except ImportError as e:
        return jsonify({"success": False, "error": "missing_module", "module": getattr(e, 'name', None) or 'reportlab'}), 503
    except Exception as e:
        app_logger.error(f"[QUOTE] Modification : échec PDF : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    try:
        number, client, desc, details, qty, unit_price, total, total_value, notes, discount = _quote_fields(data)
        pdf_name, json_name = _write_quote_files(session['user_id'], qid, data, pdf_bytes)
        conn = get_db()
        try:
            conn.execute("""UPDATE quotes SET client=?, item_desc=?, item_details=?, qty=?, unit_price=?, total=?, total_value=?,
                            notes=?, discount_value=?, pdf_file=?, payload_file=?, client_id=? WHERE id=? AND user_id=?""",
                         (client, desc, details, qty, unit_price, total, total_value, notes, discount, pdf_name, json_name,
                          _int_or0(data.get('client_id')), qid, session['user_id']))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        app_logger.error(f"[QUOTE] Modification : enregistrement impossible : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": True, "id": qid})

def _next_invoice_number(conn, user_id, prefix, types=('invoice', 'deposit')):
    year = datetime.datetime.now().year
    best = 0
    marks = ','.join('?' * len(types))
    for r in conn.execute(f"SELECT number FROM quotes WHERE user_id = ? AND doc_type IN ({marks}) AND number LIKE ?",
                          (user_id, *types, f"%-{year}-%")).fetchall():
        mt = re.search(r'-(\d+)$', r['number'] or '')
        if mt:
            best = max(best, int(mt.group(1)))
    return f"{prefix}-{year}-{best + 1:04d}"

def api_quote_history_invoice(qid):
    """Crée la facture définitive d'un devis existant (numéro séquentiel attribué par le serveur)."""
    _ensure_quote_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({"success": False, "error": "not_found"}), 404
    if (row['doc_type'] or 'quote') != 'quote':
        return jsonify({"success": False, "error": "not_a_quote"}), 400
    data = request.get_json(silent=True) or {}
    prefix = re.sub(r'[^A-Za-z0-9]', '', str(data.get('number_prefix') or ''))[:6].upper() or 'INV'
    conn = get_db()
    try:
        existing = conn.execute("SELECT id, number FROM quotes WHERE source_quote_id = ? AND doc_type = 'invoice' AND user_id = ?",
                                (qid, session['user_id'])).fetchone()
        if existing:
            return jsonify({"success": False, "error": "invoice_exists", "id": existing['id'], "number": existing['number']}), 409
        number = _next_invoice_number(conn, session['user_id'], prefix)
    finally:
        conn.close()
    data['number'] = number
    data['ref_value'] = row['number']
    data.setdefault('client_id', row['client_id'] or 0)
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _unicodedata.normalize('NFD', str(data.get('client') or '')).encode('ascii', 'ignore').decode()).strip('-')[:40]
    file_prefix = re.sub(r'[^\w\- ]', '', str(data.get('filename_prefix') or 'Invoice'), flags=re.U)[:30] or 'Invoice'
    data['filename'] = _safe_quote_pdf_filename('-'.join(x for x in (file_prefix, slug, number) if x))
    try:
        pdf_bytes = _build_quote_pdf_with_repair(data)
    except ImportError as e:
        return jsonify({"success": False, "error": "missing_module", "module": getattr(e, 'name', None) or 'reportlab'}), 503
    except Exception as e:
        app_logger.error(f"[QUOTE] Facture : échec PDF : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    new_id = _record_quote(session['user_id'], data, pdf_bytes, doc_type='invoice', source_id=qid)
    if not new_id:
        return jsonify({"success": False, "error": "record_failed"}), 500
    app_logger.info(f"[QUOTE] 🧾 Facture {number} créée d'après le devis {row['number']}")
    return jsonify({"success": True, "id": new_id, "number": number})

# --- suivi des paiements, avoirs / acomptes, carnet de clients, e-mail, export comptable ---
_QUOTE_STATUSES = {'quote': ('draft', 'sent', 'accepted', 'refused'), 'invoice': ('draft', 'sent', 'paid'),
                   'deposit': ('draft', 'sent', 'paid'), 'credit': ('draft', 'sent')}

def api_quote_set_status(qid):
    _ensure_quote_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({"success": False, "error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    dt = row['doc_type'] or 'quote'
    sets, args = [], []
    if 'status' in data:
        st = str(data.get('status') or '')
        if st not in _QUOTE_STATUSES.get(dt, ()):
            return jsonify({"success": False, "error": "bad_status"}), 400
        today = datetime.date.today().isoformat()
        sets.append('status=?'); args.append(st)
        sets.append('paid_at=?'); args.append(today if st == 'paid' else '')
        if st == 'sent' and not row['sent_at']:
            sets.append('sent_at=?'); args.append(today)
    if 'due_date' in data:
        sets.append('due_date=?'); args.append(_iso_date(data.get('due_date')))
    if not sets:
        return jsonify({"success": False, "error": "nothing"}), 400
    conn = get_db()
    try:
        conn.execute(f"UPDATE quotes SET {', '.join(sets)} WHERE id=? AND user_id=?", (*args, qid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    created = 0
    if data.get('status') == 'accepted':
        try:
            created = _MAIN['_create_jobs_from_quote'](session['user_id'], row)
        except Exception as e:
            app_logger.warning(f"[Atelier] Création de tâches impossible : {e}")
    return jsonify({"success": True, "jobs_created": created})

def api_quotes_summary():
    """Résumé pour le tableau de bord : factures en retard, montant à encaisser, devis en attente."""
    _ensure_quote_columns()
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM quotes WHERE user_id = ? AND doc_type IN ('invoice','deposit','quote')", (session['user_id'],)).fetchall()
    finally:
        conn.close()
    today = datetime.date.today()
    overdue, unpaid, pending = [], 0.0, 0
    for r in rows:
        dt = r['doc_type'] or 'quote'
        if dt == 'quote':
            if (r['status'] or 'draft') == 'sent':
                pending += 1
            continue
        if (r['status'] or 'draft') == 'paid':
            continue
        unpaid += float(r['total_value'] or 0)
        if _quote_eff_status(r) == 'overdue':
            try:
                late = (today - datetime.date.fromisoformat(r['due_date'])).days
            except Exception:
                late = 0
            overdue.append({"id": r['id'], "number": r['number'], "client": r['client'], "total": r['total'],
                            "due_date": r['due_date'], "days_late": late})
    overdue.sort(key=lambda x: -x['days_late'])
    return jsonify({"overdue": overdue, "unpaid_total": round(unpaid, 2), "pending_quotes": pending})

def _derive_document(qid, doc_type, number_types, default_prefix):
    """Crée un document dérivé (facture d'acompte, avoir) à partir d'un document existant ; numéro attribué par le serveur."""
    _ensure_quote_columns()
    row = _stored_quote(qid)
    if not row:
        return jsonify({"success": False, "error": "not_found"}), 404
    src_type = row['doc_type'] or 'quote'
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('total_value') or 0)
    except (TypeError, ValueError):
        amount = 0.0
    conn = get_db()
    try:
        if doc_type == 'deposit':
            if src_type != 'quote':
                return jsonify({"success": False, "error": "not_a_quote"}), 400
            if conn.execute("SELECT 1 FROM quotes WHERE source_quote_id = ? AND doc_type = 'invoice'", (qid,)).fetchone():
                return jsonify({"success": False, "error": "invoice_exists"}), 409
            done = conn.execute("SELECT COALESCE(SUM(total_value),0) FROM quotes WHERE source_quote_id = ? AND doc_type = 'deposit'", (qid,)).fetchone()[0]
            if amount <= 0 or done + amount > float(row['total_value'] or 0) + 0.005:
                return jsonify({"success": False, "error": "amount_too_high", "remaining": round(float(row['total_value'] or 0) - done, 2)}), 400
        else:  # avoir
            if src_type not in ('invoice', 'deposit'):
                return jsonify({"success": False, "error": "not_an_invoice"}), 400
            amount = -abs(amount)
            done = conn.execute("SELECT COALESCE(SUM(-total_value),0) FROM quotes WHERE source_quote_id = ? AND doc_type = 'credit'", (qid,)).fetchone()[0]
            if amount == 0 or done + abs(amount) > float(row['total_value'] or 0) + 0.005:
                return jsonify({"success": False, "error": "amount_too_high", "remaining": round(float(row['total_value'] or 0) - done, 2)}), 400
            data['total_value'] = amount
        prefix = re.sub(r'[^A-Za-z0-9]', '', str(data.get('number_prefix') or ''))[:6].upper() or default_prefix
        number = _next_invoice_number(conn, session['user_id'], prefix, number_types)
    finally:
        conn.close()
    data['number'] = number
    data['ref_value'] = row['number']
    data['client_id'] = row['client_id'] or data.get('client_id') or 0
    slug = re.sub(r'[^A-Za-z0-9]+', '-', _unicodedata.normalize('NFD', str(data.get('client') or '')).encode('ascii', 'ignore').decode()).strip('-')[:40]
    file_prefix = re.sub(r'[^\w\- ]', '', str(data.get('filename_prefix') or doc_type), flags=re.U)[:30] or doc_type
    data['filename'] = _safe_quote_pdf_filename('-'.join(x for x in (file_prefix, slug, number) if x))
    try:
        pdf_bytes = _build_quote_pdf_with_repair(data)
    except ImportError as e:
        return jsonify({"success": False, "error": "missing_module", "module": getattr(e, 'name', None) or 'reportlab'}), 503
    except Exception as e:
        app_logger.error(f"[QUOTE] {doc_type} : échec PDF : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    new_id = _record_quote(session['user_id'], data, pdf_bytes, doc_type=doc_type, source_id=qid)
    if not new_id:
        return jsonify({"success": False, "error": "record_failed"}), 500
    app_logger.info(f"[QUOTE] Document {doc_type} {number} créé d'après {row['number']}")
    return jsonify({"success": True, "id": new_id, "number": number})

def api_quote_deposit(qid):
    return _derive_document(qid, 'deposit', ('invoice', 'deposit'), 'FAC')

def api_quote_credit(qid):
    return _derive_document(qid, 'credit', ('credit',), 'AV')

# ---- Carnet de clients ----
_CLIENT_FIELDS = (('name', 120), ('email', 120), ('phone', 40), ('address', 300), ('tax_id', 60), ('notes', 500))

def _client_clean(data):
    out = {}
    for k, lim in _CLIENT_FIELDS:
        out[k] = str(data.get(k) or '').strip()[:lim]
    return out

# ── clients (carnet de clients, import) : module séparé `modules/clients.py` (services fournis par `clients.init(globals())`) ──
from modules import clients

from modules.clients import (
    api_client_delete,
    api_client_detail,
    api_client_update,
    api_clients_create,
    api_clients_import,
    api_clients_list,
)

# ---- Export comptable (CSV) ----
_CSV_HEAD = {
    'fr': ['Numéro', 'Type', 'Date', 'Client', 'N° SIRET / TVA client', 'Désignation', 'Quantité', 'Sous-total', 'Remise', 'Total', 'Statut',
           'Échéance', 'Date de paiement', 'Document d\'origine'],
    'en': ['Number', 'Type', 'Date', 'Customer', 'Customer tax ID', 'Description', 'Quantity', 'Subtotal', 'Discount', 'Total', 'Status',
           'Due date', 'Payment date', 'Source document']}

_CSV_TYPES = {'fr': {'quote': 'Devis', 'invoice': 'Facture', 'deposit': 'Facture d\'acompte', 'credit': 'Avoir'},
              'en': {'quote': 'Quote', 'invoice': 'Invoice', 'deposit': 'Deposit invoice', 'credit': 'Credit note'}}

_CSV_STATUS = {'fr': {'draft': 'Brouillon', 'sent': 'Envoyé', 'accepted': 'Accepté', 'refused': 'Refusé', 'paid': 'Payé', 'overdue': 'En retard'},
               'en': {'draft': 'Draft', 'sent': 'Sent', 'accepted': 'Accepted', 'refused': 'Refused', 'paid': 'Paid', 'overdue': 'Overdue'}}

def _quotes_csv_bytes(user_id, date_from, date_to, types, lang):
    import csv
    lg = 'fr' if lang == 'fr' else 'en'
    dec = ',' if lg == 'fr' else '.'
    conn = get_db()
    try:
        rows = conn.execute("""SELECT q.*, s.number AS src_number, c.tax_id AS client_tax_id
                               FROM quotes q LEFT JOIN quotes s ON s.id = q.source_quote_id
                               LEFT JOIN clients c ON c.id = q.client_id
                               WHERE q.user_id = ? ORDER BY q.created_at, q.id""", (user_id,)).fetchall()
    finally:
        conn.close()
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    w.writerow(_CSV_HEAD[lg])

    def num(v):
        return f"{float(v or 0):.2f}".replace('.', dec)
    for r in rows:
        dt = r['doc_type'] or 'quote'
        day = str(r['created_at'] or '')[:10]
        if types and dt not in types:
            continue
        if (date_from and day < date_from) or (date_to and day > date_to):
            continue
        tv = float(r['total_value'] or 0)
        disc = float(r['discount_value'] or 0)
        w.writerow([r['number'], _CSV_TYPES[lg].get(dt, dt), day, r['client'], r['client_tax_id'] or '', r['item_desc'], r['qty'],
                    num(tv + disc), num(disc), num(tv), _CSV_STATUS[lg].get(_quote_eff_status(r), ''), r['due_date'] or '',
                    r['paid_at'] or '', r['src_number'] or ''])
    return ('﻿' + buf.getvalue()).encode('utf-8')

def _csv_args(src):
    types = [t for t in str(src.get('types') or '').split(',') if t in ('quote', 'invoice', 'deposit', 'credit')]
    return _iso_date(src.get('from')), _iso_date(src.get('to')), types, str(src.get('lang') or 'fr')[:2]

def api_quotes_export_csv():
    _ensure_quote_columns()
    f, t, types, lang = _csv_args(request.args)
    data = _quotes_csv_bytes(session['user_id'], f, t, types, lang)
    return Response(data, mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="stellio-export-{datetime.date.today().isoformat()}.csv"'})

def api_quotes_export_csv_native():
    _ensure_quote_columns()
    f, t, types, lang = _csv_args(request.get_json(silent=True) or {})
    data = _quotes_csv_bytes(session['user_id'], f, t, types, lang)
    try:
        import webview
        result = webview.windows[0].create_file_dialog(
            _wv_save_dialog(webview), directory=str(Path.home() / 'Documents'),
            save_filename=f"stellio-export-{datetime.date.today().isoformat()}.csv", file_types=('Fichier CSV (*.csv)',))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    dest = result[0] if isinstance(result, (list, tuple)) and result else result
    if not dest:
        return jsonify({"success": False, "cancelled": True}), 200
    dest = str(dest)
    if not dest.lower().endswith('.csv'):
        dest += '.csv'
    try:
        with open(dest, 'wb') as fh:
            fh.write(data)
        return jsonify({"success": True, "path": dest})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---- E-mail (SMTP) ----
def _smtp_cfg(override=None):
    s = dict(load_settings() or {})
    for k, v in (override or {}).items():
        if str(k).startswith('smtp_'):
            s[k] = v
    host = str(s.get('smtp_host') or '').strip()
    if not host:
        return None
    sec = str(s.get('smtp_security') or 'starttls')
    try:
        port = int(s.get('smtp_port') or (465 if sec == 'ssl' else 587 if sec == 'starttls' else 25))
    except (TypeError, ValueError):
        port = 587
    user = str(s.get('smtp_user') or '').strip()
    return {'host': host, 'port': port, 'user': user, 'password': str(s.get('smtp_password') or ''), 'security': sec,
            'from': str(s.get('smtp_from') or user).strip(), 'from_name': str(s.get('smtp_from_name') or '').strip()}

def _smtp_send(cfg, to, subject, body, attachment=None):
    import smtplib
    from email.message import EmailMessage
    from email.utils import formataddr
    if not cfg['from']:
        raise ValueError('adresse expéditeur manquante')
    msg = EmailMessage()
    msg['From'] = formataddr((cfg['from_name'], cfg['from'])) if cfg['from_name'] else cfg['from']
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    if attachment:
        msg.add_attachment(attachment[1], maintype='application', subtype='pdf', filename=attachment[0])
    ctx = ssl.create_default_context()
    if cfg['security'] == 'ssl':
        srv = smtplib.SMTP_SSL(cfg['host'], cfg['port'], timeout=20, context=ctx)
    else:
        srv = smtplib.SMTP(cfg['host'], cfg['port'], timeout=20)
    try:
        srv.ehlo()
        if cfg['security'] == 'starttls':
            srv.starttls(context=ctx)
            srv.ehlo()
        if cfg['user']:
            srv.login(cfg['user'], cfg['password'])
        srv.send_message(msg)
    finally:
        try:
            srv.quit()
        except Exception:
            pass

_EMAIL_RE = re.compile(r'^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$')

def api_smtp_test():
    body = request.get_json(silent=True) or {}
    cfg = _smtp_cfg(body)
    if not cfg:
        return jsonify({"success": False, "error": "Serveur SMTP manquant"}), 200
    to = str(body.get('to') or cfg['from']).strip()
    if not _EMAIL_RE.match(to):
        return jsonify({"success": False, "error": "Adresse de destination invalide"}), 200
    try:
        _smtp_send(cfg, to, 'Stellio - test e-mail', 'Ce message confirme que la configuration SMTP de Stellio fonctionne.')
    except Exception as e:
        return jsonify({"success": False, "error": f"{type(e).__name__}: {str(e)[:140]}"}), 200
    return jsonify({"success": True, "to": to})

def api_quote_email(qid):
    _ensure_quote_columns()
    row = _stored_quote(qid)
    path = _stored_quote_path(row) if row else None
    if not path:
        return jsonify({"success": False, "error": "PDF introuvable"}), 404
    cfg = _smtp_cfg()
    if not cfg:
        return jsonify({"success": False, "error": "smtp_not_configured"}), 200
    data = request.get_json(silent=True) or {}
    to = str(data.get('to') or '').strip()
    if not _EMAIL_RE.match(to):
        return jsonify({"success": False, "error": "bad_recipient"}), 200
    subject = str(data.get('subject') or row['number'])[:200]
    message = str(data.get('message') or '')[:4000]
    try:
        with open(path, 'rb') as fh:
            pdf = fh.read()
        _smtp_send(cfg, to, subject, message, (_safe_quote_pdf_filename(row['filename'] or row['number']), pdf))
    except Exception as e:
        app_logger.warning(f"[SMTP] Envoi échoué : {type(e).__name__}: {str(e)[:120]}")
        return jsonify({"success": False, "error": f"{type(e).__name__}: {str(e)[:140]}"}), 200
    conn = get_db()
    try:
        conn.execute("UPDATE quotes SET status = CASE WHEN status IN ('', 'draft') THEN 'sent' ELSE status END, "
                     "sent_at = CASE WHEN sent_at = '' THEN ? ELSE sent_at END WHERE id = ? AND user_id = ?",
                     (datetime.date.today().isoformat(), qid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True})

def api_quote_history_pdf(qid):
    row = _stored_quote(qid)
    path = _stored_quote_path(row) if row else None
    if not path:
        return jsonify({"error": "PDF introuvable"}), 404
    inline = request.args.get('inline') == '1'
    name = _safe_quote_pdf_filename(row['filename'] or row['number'])
    if inline:
        # Les visionneuses intégrées (WebView, navigateurs mobiles) demandent un « code » pour tout PDF chiffré,
        # même quand le mot de passe utilisateur est vide : l'aperçu est donc servi sans chiffrement.
        # Le fichier téléchargé / enregistré reste verrouillé.
        try:
            pj = _quote_payload_path(row)
            if pj and os.path.isfile(pj):
                with open(pj, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                return send_file(io.BytesIO(_build_quote_pdf_with_repair(payload, encrypt=False)),
                                 mimetype='application/pdf', as_attachment=False, download_name=name)
        except Exception as e:
            app_logger.warning(f"[QUOTE] Aperçu non chiffré indisponible, repli : {e}")
        try:
            from pypdf import PdfReader, PdfWriter
            rd = PdfReader(str(path))
            if rd.is_encrypted:
                rd.decrypt('')
            wr = PdfWriter()
            for pg in rd.pages:
                wr.add_page(pg)
            out = io.BytesIO(); wr.write(out); out.seek(0)
            return send_file(out, mimetype='application/pdf', as_attachment=False, download_name=name)
        except Exception:
            pass
    return send_file(path, mimetype='application/pdf', as_attachment=not inline, download_name=name)

def api_quote_history_save_native(qid):
    row = _stored_quote(qid)
    path = _stored_quote_path(row) if row else None
    if not path:
        return jsonify({"success": False, "error": "PDF introuvable"}), 404
    try:
        import webview
        result = webview.windows[0].create_file_dialog(
            _wv_save_dialog(webview), directory=str(Path.home() / 'Documents'),
            save_filename=_safe_quote_pdf_filename(row['filename'] or row['number']),
            file_types=('Document PDF (*.pdf)',))
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    dest = result[0] if isinstance(result, (list, tuple)) and result else result
    if not dest:
        return jsonify({"success": False, "cancelled": True}), 200
    dest = str(dest)
    if not dest.lower().endswith('.pdf'):
        dest += '.pdf'
    try:
        shutil.copyfile(path, dest)
        return jsonify({"success": True, "path": dest}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def api_quote_history_delete(qid):
    row = _stored_quote(qid)
    if not row:
        return jsonify({"error": "Devis introuvable"}), 404
    path = _stored_quote_path(row)
    conn = get_db()
    try:
        keys = row.keys()
        label = (row['number'] if 'number' in keys and row['number'] else '') or f"#{qid}"
        who = (row['client'] if 'client' in keys else '') or ''
        tid = trash_record(conn, session['user_id'], 'quote', f"{label}" + (f" — {who}" if who else ''),
                           {'row': dict(row)}, detail=(row['doc_type'] if 'doc_type' in keys and row['doc_type'] else 'quote'),
                           files=[path, _quote_payload_path(row)])
        conn.execute("DELETE FROM quotes WHERE id = ? AND user_id = ?", (qid, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True, "trash_key": f"row:{tid}"})

def api_quote_export_native():
    data = request.get_json(silent=True) or {}
    filename = _safe_quote_pdf_filename(data.get('filename'))
    try:
        pdf_bytes = _build_quote_pdf_with_repair(data)
    except ImportError as e:
        app_logger.error(f"[QUOTE] Échec génération PDF : {e}")
        return jsonify({"success": False, "error": "missing_module", "module": getattr(e, 'name', None) or 'reportlab'}), 503
    except Exception as e:
        app_logger.error(f"[QUOTE] Échec génération PDF : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    try:
        import webview
        result = webview.windows[0].create_file_dialog(
            _wv_save_dialog(webview),
            directory=str(Path.home() / 'Documents'),
            save_filename=filename,
            file_types=('Document PDF (*.pdf)',)
        )
    except Exception as e:
        app_logger.info(f"[QUOTE] Boîte de dialogue native indisponible : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    dest_path = result[0] if isinstance(result, (list, tuple)) and result else result
    if not dest_path:
        return jsonify({"success": False, "cancelled": True}), 200
    dest_path = str(dest_path)
    if not dest_path.lower().endswith('.pdf'):
        dest_path += '.pdf'

    try:
        with open(dest_path, 'wb') as f:
            f.write(pdf_bytes)
        app_logger.info(f"[QUOTE] 🧾 Devis PDF enregistré : {dest_path}")
        _record_quote(session['user_id'], data, pdf_bytes)
        return jsonify({"success": True, "path": dest_path}), 200
    except Exception as e:
        app_logger.error(f"[QUOTE] Échec écriture fichier : {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def api_quote_export():
    data = request.get_json(silent=True) or {}
    try:
        pdf_bytes = _build_quote_pdf_with_repair(data)
    except ImportError as e:
        app_logger.error(f"[QUOTE] Échec génération PDF : {e}")
        return jsonify({"success": False, "error": "missing_module", "module": getattr(e, 'name', None) or 'reportlab'}), 503
    except Exception as e:
        app_logger.error(f"[QUOTE] Échec génération PDF : {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    _record_quote(session['user_id'], data, pdf_bytes)
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True,
                     download_name=_safe_quote_pdf_filename(data.get('filename')))


_ROUTES = (
    ('/api/quote/logo', ['GET'], 'api_quote_logo_get', ('login_required', )),
    ('/api/quote/logo', ['POST'], 'api_quote_logo_set', ('login_required', )),
    ('/api/quote/logo', ['DELETE'], 'api_quote_logo_delete', ('login_required', )),
    ('/api/quotes', ['GET'], 'api_quotes_list', ('login_required', )),
    ('/api/quotes/<int:qid>/payload', ['GET'], 'api_quote_history_payload', ('login_required', )),
    ('/api/quotes/<int:qid>/update', ['POST'], 'api_quote_history_update', ('login_required', )),
    ('/api/quotes/<int:qid>/invoice', ['POST'], 'api_quote_history_invoice', ('login_required', )),
    ('/api/quotes/<int:qid>/status', ['POST'], 'api_quote_set_status', ('login_required', )),
    ('/api/quotes/summary', ['GET'], 'api_quotes_summary', ('login_required', )),
    ('/api/quotes/<int:qid>/deposit', ['POST'], 'api_quote_deposit', ('login_required', )),
    ('/api/quotes/<int:qid>/credit', ['POST'], 'api_quote_credit', ('login_required', )),
    ('/api/quotes/export.csv', ['GET'], 'api_quotes_export_csv', ('login_required', )),
    ('/api/quotes/export-csv-native', ['POST'], 'api_quotes_export_csv_native', ('login_required', )),
    ('/api/smtp/test', ['POST'], 'api_smtp_test', ('login_required', )),
    ('/api/quotes/<int:qid>/email', ['POST'], 'api_quote_email', ('login_required', )),
    ('/api/quotes/<int:qid>/pdf', ['GET'], 'api_quote_history_pdf', ('login_required', )),
    ('/api/quotes/<int:qid>/save-native', ['POST'], 'api_quote_history_save_native', ('login_required', )),
    ('/api/quotes/<int:qid>', ['DELETE'], 'api_quote_history_delete', ('login_required', )),
    ('/api/quote/export-native', ['POST'], 'api_quote_export_native', ('login_required', )),
    ('/api/quote/export', ['POST'], 'api_quote_export', ('login_required', )),
)


def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"pro_quotes.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
    g['QUOTE_LOGO_FILE'] = os.path.join(DATA_DIR, "quote_logo.png")
    g['QUOTES_DIR'] = os.path.join(DATA_DIR, 'quotes')
    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {k: g[k] for k in _EXPORTS}
