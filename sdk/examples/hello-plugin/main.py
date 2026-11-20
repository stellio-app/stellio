"""Plugin d'exemple. Stellio le lance avec l'évènement en JSON sur l'entrée standard."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'python'))   # SDK fourni avec Stellio (dépôt)
try:
    from stellio_sdk import plugin_event
    event, data = plugin_event()
except ImportError:                       # plugin autonome : lire l'entrée standard soi-même
    import json
    payload = json.loads(sys.stdin.read() or '{}'); event, data = payload.get('event', ''), payload.get('data', {})
print(f"[hello-plugin] {event} : {data.get('file_name') or data.get('printer') or '(sans détail)'}")
