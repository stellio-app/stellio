#!/usr/bin/env python3
"""Extrait un bloc de main.py vers un module `<name>.py` (modèle : print_session.py).
Usage : python tools/split_module.py <name> <ligne_début> <ligne_fin> "<docstring une ligne>" [--dry]
 - routes @app.route(...) (+ autres décorateurs) -> enregistrées dans init() ;
 - services de main.py utilisés par le bloc -> _REQUIRED (injectés par init) ;
 - noms définis dans le bloc et utilisés ailleurs dans main.py -> `from <name> import ...` à l'ancien emplacement ;
 - init(globals()) ajouté (une seule fois) juste avant `if __name__ in (...)`."""
import ast, builtins, re, sys

name, a, b, doc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
dry = '--dry' in sys.argv
STD = {'os','sys','re','io','json','time','uuid','math','shutil','socket','sqlite3','hashlib','base64','secrets','datetime','logging',
       'threading','subprocess','zipfile','tempfile','glob','urllib','struct','shlex','itertools','functools','collections',
       'queue','difflib','platform','atexit','ssl','asyncio','tarfile','rarfile','requests','np','Path','wraps','urlparse','unquote'}
src = open('main.py', encoding='utf-8').read(); L = src.split('\n')
LATE_NAMES = set()
tree = ast.parse(src)
inblk = lambda n: n.lineno >= a and n.end_lineno <= b
defs_in, defs_out, imp_names = set(), set(), {}
def defined(n):
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)): return {n.name}
    if isinstance(n, ast.Assign): return {t.id for t in n.targets if isinstance(t, ast.Name)}
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name): return {n.target.id}
    return set()
for n in tree.body:
    (defs_in if inblk(n) else defs_out).update(defined(n))
    if isinstance(n, (ast.Import, ast.ImportFrom)) and not inblk(n):
        for x in n.names: imp_names[(x.asname or x.name).split('.')[0]] = n.lineno
# noms liés dans des instructions composées de haut niveau (try/if/with…) : ex. `try: import paho… except: HAS_MQTT = False`
optional_names = set()
def _bind(node, in_try_import=False):
    for x in ast.walk(node):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)) and x is not node:
            continue
for n in tree.body:
    if inblk(n) or not isinstance(n, (ast.Try, ast.If, ast.With, ast.For, ast.While)): continue
    def walk(nodes, depth_try):
        for x in nodes:
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): continue
            if isinstance(x, (ast.Import, ast.ImportFrom)):
                for al in x.names:
                    nm_ = (al.asname or al.name).split('.')[0]; defs_out.add(nm_); imp_names.setdefault(nm_, x.lineno)
                    if depth_try: optional_names.add(nm_)
            elif isinstance(x, ast.Assign):
                for t_ in x.targets:
                    if isinstance(t_, ast.Name): defs_out.add(t_.id)
            for fld in ('body', 'orelse', 'finalbody'):
                if hasattr(x, fld) and isinstance(getattr(x, fld), list): walk(getattr(x, fld), depth_try or isinstance(x, ast.Try))
            if isinstance(x, ast.Try):
                for h in x.handlers: walk(h.body, True)
    walk([n], False)
# nœuds hors bloc qui chevauchent partiellement -> erreur
for n in tree.body:
    if (a <= n.lineno <= b) != (a <= n.end_lineno <= b): sys.exit(f"bornes coupent le nœud {n.lineno}-{n.end_lineno}")
blk_nodes = [n for n in tree.body if inblk(n)]
bi = set(dir(builtins))
used, local_assigned = set(), set()
for n in blk_nodes:
    for x in ast.walk(n):
        if isinstance(x, ast.Name): used.add(x.id)
needed = {u for u in used if u not in defs_in and u not in bi and (u in defs_out or u in imp_names)}
std_needed = {u for u in needed if u in STD}
required = sorted(needed - STD - optional_names)
optional = sorted((needed & optional_names) - STD)
# noms utilisés ailleurs dans main.py
inb = set()
for n in tree.body:
    if not inblk(n):
        for x in ast.walk(n):
            if isinstance(x, ast.Name) and x.id in defs_in: inb.add(x.id)
# main.py garde TOUS les noms du bloc (autres modules et overlay démo les lisent via les globals de main) ;
# sauf ceux réaffectés via `global` dans le bloc (l'état doit rester dans le module).
glob_names = {n for nd in blk_nodes for x in ast.walk(nd) if isinstance(x, ast.Global) for n in x.names}
for g_ in sorted(glob_names & inb): print('⚠ nom réaffecté via global ET utilisé par main.py :', g_)
inb = {n for n in defs_in if not n.startswith('__')} - glob_names - LATE_NAMES
# imports locaux du module : on réimporte tout STD vu dans main
std_imports = {'os':'import os','sys':'import sys','re':'import re','io':'import io','json':'import json','time':'import time','uuid':'import uuid','math':'import math',
 'shutil':'import shutil','socket':'import socket','sqlite3':'import sqlite3','hashlib':'import hashlib','base64':'import base64','secrets':'import secrets',
 'datetime':'import datetime','logging':'import logging','threading':'import threading','subprocess':'import subprocess','zipfile':'import zipfile','tempfile':'import tempfile',
 'glob':'import glob','urllib':'import urllib.parse','struct':'import struct','shlex':'import shlex','itertools':'import itertools','functools':'import functools',
 'collections':'import collections','queue':'import queue','difflib':'import difflib','platform':'import platform','atexit':'import atexit','ssl':'import ssl',
 'asyncio':'import asyncio','tarfile':'import tarfile','rarfile':'import rarfile','requests':'import requests','np':'import numpy as np',
 'Path':'from pathlib import Path','wraps':'from functools import wraps','urlparse':'from urllib.parse import urlparse, unquote','unquote':'from urllib.parse import urlparse, unquote'}
imports = sorted({std_imports[s] for s in std_needed})
# top-level non-def statements qui utilisent des services injectés à l'import -> problème
bad = []
late = []
routes = []
body_parts = []
for n in blk_nodes:
    seg_start = (min([d.lineno for d in n.decorator_list]) if getattr(n, 'decorator_list', None) else n.lineno)
    # inclure commentaires juste au-dessus
    s = seg_start
    while s - 2 >= 0 and L[s - 2].startswith('#') and s - 1 > (a - 1): s -= 1
    text = '\n'.join(L[s - 1:n.end_lineno])
    if isinstance(n, ast.FunctionDef) and n.decorator_list:
        rdec = [d for d in n.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == 'route']
        if rdec:
            r = rdec[0]; rule = ast.get_source_segment(src, r.args[0])
            methods = ast.get_source_segment(src, next((k.value for k in r.keywords if k.arg == 'methods'), ast.parse("['GET']").body[0].value))
            others = [ast.get_source_segment(src, d) for d in n.decorator_list if d is not r]
            routes.append((rule, methods, n.name, others))
            for d in n.decorator_list:
                text = text.replace('@' + ast.get_source_segment(src, d) + '\n', '', 1) if ('@' + ast.get_source_segment(src, d) + '\n') in text else text
        else:
            other_names = {x.id for d in n.decorator_list for x in ast.walk(d) if isinstance(x, ast.Name)}
            if other_names & set(required): bad.append(f"décorateur non-route à la ligne {n.lineno}")
    elif not isinstance(n, (ast.FunctionDef, ast.ClassDef)):
        names = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
        if names & set(required):
            if isinstance(n, ast.Assign) and all(isinstance(t_, ast.Name) for t_ in n.targets):
                late.append((n, [t_.id for t_ in n.targets], ast.get_source_segment(src, n.value)))
                continue
            bad.append(f"instruction de niveau module ligne {n.lineno} utilise {sorted(names & set(required))}")
    body_parts.append(text)
dec_names = {x.id for r in routes for d in r[3] for x in ast.walk(ast.parse(d)) if isinstance(x, ast.Name)}
required_all = sorted(set(required) | ({'app'} if routes else set()) | (dec_names & (defs_out | set(imp_names))))
print(f"module {name}: {b-a+1} lignes, {len(blk_nodes)} éléments, {len(routes)} routes, {len(required_all)} services, {len(inb)} noms réimportés")
print("services :", required_all)
print("réimportés :", sorted(inb))
if bad: print("⚠ À TRAITER À LA MAIN :", *bad, sep='\n  ')
if dry or bad: sys.exit(1 if bad else 0)
body = '\n\n'.join(body_parts).rstrip() + '\n'
body = body.replace("globals().get(", "_MAIN.get(")   # les globals de main.py se lisent via _MAIN
head = f'"""Stellio — {doc}\n\nModule séparé de main.py (même schéma que print_session.py) : main.py appelle `{name}.init(globals())` une fois\ntoutes ses fonctions définies ; init() reçoit les services de main.py puis enregistre les routes.\nGénéré avec tools/split_module.py ; les tests importent ce module directement avec de faux services.\n"""\n'
head += '\n'.join(imports) + '\n\n' if imports else '\n'
head += f"_REQUIRED = (\n" + ''.join(f"    '{r}',\n" for r in required_all) + ")\n"
head += "_OPTIONAL = (" + ''.join(f"'{o}', " for o in optional) + ")   # fournis seulement s'ils existent dans main.py (import facultatif)\n"
head += "_OVERRIDABLE = (" + ''.join(f"'{s}', " for s in sorted(std_needed)) + ")\n\n"
head += "_MAIN = {}   # globals de main.py (vue vivante) : pour les noms définis plus tard, ex. _MAIN.get('SERVER_PORT')\n"
head += ''.join(f"{o} = None\n" for o in optional)
head += '# Valeurs réelles posées par init() (None tant que le module n\'est pas branché).\n' + ''.join(f"{r} = None\n" for r in required_all) + '\n\n'
tail = '\n\n_ROUTES = (\n' + ''.join(f"    ({r[0]}, {r[1]}, '{r[2]}', ({''.join(repr(o)+', ' for o in r[3])})),\n" for r in routes) + ')\n\n\n'
late_names = [x for _, ns_, _ in late for x in ns_]
late_code = ''.join(f"    g['{nm}'] = {val}\n" for _, ns_, val in late for nm in ns_[:1]) + ''.join(f"    g['{nm}'] = g['{ns_[0]}']\n" for _, ns_, _ in late for nm in ns_[1:])
tail += '''def init(ns, routes=True):
    """Reçoit les services de main.py (dict des globals) et enregistre les routes Flask."""
    g = globals()
    g['_MAIN'] = ns
    missing = [n for n in _REQUIRED if n not in ns]
    if missing:
        raise RuntimeError(f"%s.init : services manquants : {missing}")
    for n in _REQUIRED + _OPTIONAL + _OVERRIDABLE:
        if n in ns:
            g[n] = ns[n]
@@LATE@@    if routes:
        for rule, methods, fname, decos in _ROUTES:
            view = g[fname]
            for d in reversed(decos):
                view = eval(d, g)(view)
            g['app'].add_url_rule(rule, endpoint=fname, view_func=view, methods=methods)
    return {@@LATEDICT@@}
''' % name
tail = tail.replace('@@LATE@@', late_code).replace('@@LATEDICT@@', ', '.join(f"'{n}': g['{n}']" for n in late_names))
for n_ in late_names: head += f"{n_} = None\n"
open(f'{name}.py', 'w', encoding='utf-8').write(head + body + tail)
# main.py : remplace le bloc
inb = inb - set(late_names)
imp = ''
if inb:
    names = sorted(inb)
    imp = f"from {name} import (\n" + ''.join(f"    {n},\n" for n in names) + ")\n"
repl = [f"# ── {doc} : module séparé `{name}.py` (services fournis par `{name}.init(globals())`) ──", f"import {name}"] + ([imp.rstrip()] if imp else []) + ['']
L[a - 1:b] = repl
out = '\n'.join(L)
mk = "\nif __name__ in ('__main__', 'stellio_main'):\n"
assert out.count(mk) == 1
call = f"{name}.init(globals())" if not late_names else f"globals().update({name}.init(globals()))"
out = out.replace(mk, f"\n{call}\n" + mk, 1)
open('main.py', 'w', encoding='utf-8').write(out)
# empaquetage : build-and-sign.yml (déclencheur + listes uniques de modules copiés dans app/ : Windows, macOS, Linux)
y = open('build-and-sign.yml', encoding='utf-8').read()
if f"- '{name}.py'" not in y:
    y = y.replace("      - 'check_deps.py'\n", f"      - 'check_deps.py'\n      - '{name}.py'\n", 1)
    y = re.sub(r'(\$mods = @\([^)]*)\)', lambda m_: m_.group(1) + f',"{name}")', y)
    y = re.sub(r'(MODULES="[^"]*)"', lambda m_: m_.group(1) + f' {name}"', y)
    open('build-and-sign.yml', 'w', encoding='utf-8').write(y)
import subprocess
r = subprocess.run([sys.executable, '-m', 'pyflakes', f'{name}.py'], capture_output=True, text=True).stdout
und = [l for l in r.splitlines() if 'undefined name' in l]
if und: print('⚠ noms indéfinis (définis plus tard dans main.py ? utiliser _MAIN.get) :', *und, sep='\n  ')
print("ok : main.py mis à jour")
