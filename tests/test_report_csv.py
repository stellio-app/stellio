"""1.2.2 : export CSV du bilan d'impression."""
import datetime, importlib.util, logging, os
import pytest
flask = pytest.importorskip('flask')
from conftest import ROOT


def _client(captured):
    spec = importlib.util.spec_from_file_location('report_csv_t', os.path.join(ROOT, 'modules', 'report_csv.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    app = flask.Flask('t'); app.secret_key = 'x'

    class Conn:
        def close(self): captured['closed'] = True

    def data_range(conn, uid, a, b):
        captured.setdefault('ranges', []).append((uid, a, b))
        return {'totals': {'prints': 3, 'success': 2, 'failed': 1, 'grams': 41.5, 'seconds': 7200, 'total_cost': 1.234},
                'by_printer': [{'name': 'P1S', 'prints': 3, 'failed': 1, 'grams': 41.5, 'seconds': 7200, 'cost': 1.234}],
                'by_material': [{'name': '=cmd|calc', 'prints': 3, 'failed': 1, 'grams': 41.5, 'seconds': 7200, 'cost': 1.2}],
                'top_models': []}

    def bounds(freq, anchor):
        s = anchor.replace(day=1)
        return s, (s + datetime.timedelta(days=32)).replace(day=1)
    m.init(dict(REPORT_FREQUENCIES=('week', 'month', 'quarter', 'year'), _report_data_range=data_range, _report_period_bounds=bounds, app=app,
                get_db=lambda: Conn(), login_required=lambda f: f, request=flask.request, session=flask.session))
    c = app.test_client()
    with c.session_transaction() as s:
        s['user_id'] = 5
    return c


def test_csv_bilan_contenu_et_en_tetes():
    cap = {}
    r = _client(cap).get('/api/reports/period.csv?frequency=month&date=2026-11-15')
    assert r.status_code == 200 and r.mimetype == 'text/csv'
    assert 'bilan-month-2026-11-01.csv' in r.headers['Content-Disposition']
    txt = r.get_data(as_text=True)
    assert txt.startswith('﻿') and 'prints;3' in txt and 'grams;41.5' in txt and 'total_cost;1.23' in txt
    assert 'P1S;3;1;41.5;7200;1.23' in txt and 'periode_precedente' in txt
    assert [x[0] for x in cap['ranges']] == [5, 5] and cap['closed']                    # période courante + précédente, connexion fermée


def test_csv_neutralise_les_formules():
    txt = _client({}).get('/api/reports/period.csv').get_data(as_text=True)
    assert "'=cmd|calc" in txt and '\n=cmd' not in txt


def test_frequence_inconnue_retombe_sur_mois():
    r = _client({}).get('/api/reports/period.csv?frequency=zz&date=2026-02-10')
    assert 'bilan-month-2026-02-01.csv' in r.headers['Content-Disposition']
