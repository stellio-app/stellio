"""Modules séparés de main.py (Stellio).

Chaque module regroupe une fonction de l'application (routes + code associé) et expose `init(globals())`,
appelé par main.py une fois ses services définis. Voir CODEMAP.md (section « Modules séparés ») et tools/split_module.py.
Ajouter un module : `python tools/split_module.py <nom> <ligne_début> <ligne_fin> "<description>"`.
"""
ALL = (
    'print_session',
    'share_link',
    'order_tracking',
    'timelapse',
    'mqtt_publisher',
    'tigertag',
    'push_notify',
    'auto_backup_routes',
    'feedback',
    'sosprint_helpers',
    'remote_instances',
    'slicer_profiles',
    'clients',
    'trash_routes',
    'quote_portal',
    'accounting_zip',
    'parts_stock',
    'printer_dispatch',
    'digest',
    'filament_weighing',
    'profile_share',
    'openprinttag',
    'open_filament_db',
)
