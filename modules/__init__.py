"""Modules séparés de main.py (Stellio).

Chaque module regroupe une fonction de l'application (routes + code associé) et expose `init(globals())`,
appelé par main.py une fois ses services définis. Voir CODEMAP.md (section « Modules séparés ») et tools/split_module.py.
Ajouter un module : `python tools/split_module.py <nom> <ligne_début> <ligne_fin> "<description>"`.
"""
# Plugins intégrés (1.1.7) : leurs modules vivent dans bundled_plugins/<id>/ mais restent importables comme `modules.<nom>` ;
# main.py ne les initialise que si le plugin est activé (voir plugin_host.py).
import os as _os
_BUNDLED = _os.environ.get('STELLIO_BUNDLED_PLUGINS') or _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'bundled_plugins')
if _os.path.isdir(_BUNDLED):
    for _n in sorted(_os.listdir(_BUNDLED)):
        _d = _os.path.join(_BUNDLED, _n)
        if _os.path.isfile(_os.path.join(_d, 'plugin.json')):
            __path__.append(_d)
ALL = (
    'print_session',
    'tigertag',
    'auto_backup_routes',
    'feedback',
    'sosprint_helpers',
    'slicer_profiles',
    'trash_routes',
    'printer_dispatch',
    'filament_weighing',
    'openprinttag',
    'open_filament_db',
    'slicer_import',
    'ai_providers',
    'workshop_watch',
    'print_traceability',
    'public_api',
    'backup_restore',
    'integrity_check',
    'account_platforms',
    'gcode_archive',
    'trash_core',
    'file_origin_delete',
    'login_log',
    'session_manager',
    'print_gcode_archive',
    'plugins',
    'shape_search',
    'model_lighten',
    'model_diff',
    'auto_organize',
    'compat',
    'part_dossier',
    'print_check',
    'access_control',
    'audit_log',
    'license_watch',
    'print_enrich',
    'migrations',
    'job_manager',
    'model_versions',
    'printers_extra',
    'failure_stats',
    'intelligence',
    'collections_sets',
    'plugin_host',
    'print_events',
)
