"""Modèle de plugin Stellio : lit l'évènement sur l'entrée standard."""
import json, os, sys

payload = json.loads(sys.stdin.read() or "{}")
event, data = payload.get("event", ""), payload.get("data", {})
config = json.loads(os.environ.get("STELLIO_PLUGIN_CONFIG") or "{}")

print(f"{event}: {data.get('file_name') or data.get('printer') or '-'}")
