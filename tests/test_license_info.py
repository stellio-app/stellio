"""1.1.6 — licence d'un modèle : usage commercial déduit du texte saisi."""
import importlib.util, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _mod():
    spec = importlib.util.spec_from_file_location('file_origin_delete_t', os.path.join(ROOT, 'modules', 'file_origin_delete.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_licences_courantes():
    li = _mod().license_info
    yes = ['CC0', 'cc by', 'CC BY 4.0', 'CC-BY-SA 4.0', 'CC BY-ND', 'MIT', 'GPL-3.0', 'Apache 2.0', 'Public domain', 'domaine public', 'BSD']
    no = ['CC BY-NC', 'CC BY-NC-SA 4.0', 'CC-BY-NC-ND', 'Standard Digital File License', 'Personal use only', 'usage personnel', 'non-commercial',
          'All rights reserved', 'Tous droits réservés']
    for t in yes:
        assert li(t)['commercial'] == 'yes', t
    for t in no:
        assert li(t)['commercial'] == 'no', t
    for t in ('', '   ', 'licence maison', 'voir le site', None):
        assert li(t)['commercial'] == 'unknown', t


def test_identifiants():
    li = _mod().license_info
    assert li('cc by-sa')['id'] == 'CC BY-SA' and li('CC BY-NC-SA 4.0')['id'] == 'CC BY-NC-SA' and li('CC BY-NC-ND')['id'] == 'CC BY-NC-ND'
    assert li('CC0')['id'] == 'CC0' and li('mit')['id'] == 'MIT'


def test_restriction_prioritaire_sur_la_permission():
    li = _mod().license_info
    assert li('CC BY mais usage personnel uniquement')['commercial'] == 'no'    # le doute profite à l'auteur


def test_branchements_licence():
    m = _mod()
    assert 'CC BY-NC' in m.LICENSE_PRESETS and all(m.license_info(p)['commercial'] in ('yes', 'no') for p in m.LICENSE_PRESETS)
    src = open(os.path.join(ROOT, 'modules', 'file_origin_delete.py'), encoding='utf-8').read()
    assert "'/api/files/license-info'" in src and "out['license_info']" in src
    js = open(os.path.join(ROOT, 'interface', 'script.js'), encoding='utf-8').read()
    assert 'origin-license-badge' in js and '_initLicenseBadge();' in js
    for lg in ('fr', 'en', 'de', 'es', 'pt', 'it', 'zh', 'ja'):
        d = json.load(open(os.path.join(ROOT, 'languages', lg + '.json'), encoding='utf-8'))
        assert d['license.commercial_yes'] and d['license.commercial_no'] and d['license.commercial_unknown']
