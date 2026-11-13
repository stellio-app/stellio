"""v1.0.7 — photo de fin d'impression prise quand l'impression arrive à 100 % (et non 15 s après l'arrêt)."""
import importlib.util, os, time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Log:
    def info(self, m): pass
    warning = error = info


def _ps():
    spec = importlib.util.spec_from_file_location('print_session_107', os.path.join(ROOT, 'modules', 'print_session.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._V104_SESS.clear()
    mod.app_logger = _Log()
    mod._server_t = lambda k, d: d
    mod.shots, mod.saved = [], []
    mod._timelapse_grab_frame = lambda p: mod.shots.append(time.time()) or b'\xff\xd8fake\xff\xd9'
    mod._v104_save_photo = lambda uid, pid, f, jpg, kind, note: mod.saved.append((f, kind))
    return mod


def _wait(cond, t=3.0):
    end = time.time() + t
    while time.time() < end and not cond():
        time.sleep(0.02)
    return cond()


PRINTER = {'id': 1, 'user_id': 1, 'name': 'Voron', 'config': {'end_photo': True}}


def _st(phase, pct=0, f='cube.gcode'):
    return {'status': phase, 'progress': pct, 'file': f}


def test_photo_is_taken_at_100_percent_not_after_the_stop():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 40), now)
    sess = ps._V104_SESS[1]
    sess['start'] = now - 900
    ps._v104_step(PRINTER, _st('printing', 96), now + 10)
    assert sess['near_end'] and not ps.shots and ps._v104_loop_delay() == 1.0       # approche de la fin : boucle plus serrée
    ps._v104_step(PRINTER, _st('printing', 100), now + 12)
    assert _wait(lambda: sess['photo_jpg'])                                          # photo prise AVANT l'arrêt de l'imprimante
    assert len(ps.shots) == 1
    ps._v104_step(PRINTER, _st('idle'), now + 20)
    assert sess['near_end'] is False and ps._v104_loop_delay() == 5
    ps._v104_step(PRINTER, _st('idle'), now + 40)                                    # 15 s de repos : fin confirmée
    assert _wait(lambda: ps.saved)
    assert ps.saved == [('cube.gcode', 'success')] and len(ps.shots) == 1            # la photo de 100 % est celle enregistrée


def test_photo_not_repeated_within_20_seconds_but_renewed_after():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 50), now)
    sess = ps._V104_SESS[1]
    ps._v104_step(PRINTER, _st('printing', 100), now + 1)
    assert _wait(lambda: sess['photo_jpg'])
    ps._v104_step(PRINTER, _st('printing', 100), time.time() + 5)
    time.sleep(0.2)
    assert len(ps.shots) == 1
    sess['photo_ts'] -= 30
    ps._v104_step(PRINTER, _st('printing', 100), time.time() + 6)
    assert _wait(lambda: len(ps.shots) == 2)


def test_printer_without_progress_gets_photo_at_first_rest_poll():
    ps = _ps()
    now = 1000.0
    ps._v104_step(PRINTER, _st('printing', 0), now)
    sess = ps._V104_SESS[1]
    sess['start'] = now - 900
    ps._v104_step(PRINTER, _st('idle'), now + 5)                                     # 1er relevé au repos : photo tout de suite
    assert _wait(lambda: sess['photo_jpg'])
    ps._v104_step(PRINTER, _st('idle'), now + 25)
    assert _wait(lambda: ps.saved) and len(ps.shots) == 1


def test_no_early_photo_when_option_is_off():
    ps = _ps()
    off = {'id': 2, 'user_id': 1, 'name': 'X', 'config': {'meter': None}}
    ps._v104_step(off, _st('printing', 100), 1000.0)
    assert 2 not in ps._V104_SESS and not ps.shots


def test_finish_falls_back_to_a_late_grab_when_no_early_photo():
    ps = _ps()
    sess = ps._v104_new_session(PRINTER, _st('printing', 10), 1000.0)
    sess['start'] = 0.0
    ps._v104_finish(PRINTER, sess, 'idle', 2000.0)
    assert ps.saved == [('cube.gcode', 'success')] and len(ps.shots) == 1

def test_forecast_slot_uses_the_inventory_banner_style():
    html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    i = html.index('id="filament-forecast-section"')
    block = html[i:i + 900]
    assert 'inv-section' in html[i - 20:i + 120] and 'source-banner' in block and 'data-mg-slot="fil"' in block
    assert '<details class="mg-slot-details viewer-hide" style="margin-top:24px;"' not in html


def test_forecast_section_has_card_grid_banner_and_always_visible_weigh_form():
    html = open(os.path.join(ROOT, 'interface', 'index.html'), encoding='utf-8').read()
    js = open(os.path.join(ROOT, 'interface', 'management.js'), encoding='utf-8').read()
    i = html.index('id="filament-forecast-section"')
    assert 'filRefresh()' in html[i:i + 1500] and 'data-mg-slot-sub="fil"' in html[i:i + 1500]
    v = js[js.index('async function vFil'):js.index('async function filRefresh')]
    assert 'grid-spoolman' in v and 'spool-card' in v and 'f_no_manual' in v and '/api/filament/tigertag' in v
    assert 'filRefresh' in js[js.index('window.StellioManagement'):]


def test_printer_badge_sits_left_of_scroll_top_arrow():
    css = open(os.path.join(ROOT, 'interface', 'style.css'), encoding='utf-8').read()
    assert '#bottom-stack:has(> .scroll-to-top.visible) > .mini-printer-widget' in css
    assert 'right: 60px !important' in css and 'body.has-scroll-top' not in css


def test_forecast_section_only_lists_spools_about_to_run_out():
    js = open(os.path.join(ROOT, 'interface', 'management.js'), encoding='utf-8').read()
    v = js[js.index('async function vFil'):js.index('async function filRefresh')]
    assert 'FIL_ALERT_DAYS' in js and 'f.days_left > FIL_ALERT_DAYS' in v and "t('f_ok')" in v


def test_ai_alert_does_not_mark_end_photo_failed_nor_create_second_photo():
    ps = _ps()
    sess = ps._v104_new_session(PRINTER, _st('printing', 10), 1000.0)
    sess['start'] = 0.0
    sess['ai_alerted'] = True
    sess['ai_reason'] = 'spaghetti'
    notes = []
    ps._v104_save_photo = lambda uid, pid, f, jpg, kind, note: notes.append((kind, note))
    ps._v104_finish(PRINTER, sess, 'idle', 2000.0)
    assert len(notes) == 1 and notes[0][0] == 'success' and 'spaghetti' in notes[0][1]
    ps._v104_finish(PRINTER, sess, 'error', 2000.0)
    assert notes[-1][0] == 'failed'


def test_photo_result_can_be_changed_from_the_gallery():
    main = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    assert "methods=['PATCH']" in main and 'def api_update_print_photo' in main
    assert 'togglePrintPhotoResult' in js and js.count('${photoResultBadge(p)}') == 2
