"""v1.0.7 — les imprimantes configurées apparaissent toujours dans l'export des logs et dans les issues GitHub."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = open(os.path.join(ROOT, 'main.py'), encoding='utf-8').read()
FB = open(os.path.join(ROOT, 'modules', 'feedback.py'), encoding='utf-8').read()


def test_diagnostic_always_lists_printers_without_secrets():
    a = MAIN.index('def _printers_tech_summary')
    b = MAIN.index('def _collect_diagnostic_info')
    block = MAIN[a:b]
    assert "SELECT type, config, is_connected FROM printers" in block
    for secret in ('api_key', 'ip', 'name', 'serial'):
        assert f"SELECT type, config, is_connected FROM printers" in block and f"r['{secret}']" not in block
    assert "info['printers'] = _printers_tech_summary()" in MAIN


def test_issue_description_gets_printer_block_when_tech_info_is_sent():
    assert "_MAIN.get('_printers_tech_summary')" in FB and '**Imprimantes (' in FB
    assert "payload['description']" in FB
