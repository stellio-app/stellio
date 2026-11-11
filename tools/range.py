#!/usr/bin/env python3
"""Donne « début fin » (lignes de main.py) du bloc allant du 1er au dernier nom de haut niveau indiqué (décorateurs inclus)."""
import ast, sys
src = open('main.py', encoding='utf-8').read(); L = src.split('\n'); tree = ast.parse(src)
def nm(n):
    if isinstance(n, (ast.FunctionDef, ast.ClassDef)): return n.name
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name): return n.targets[0].id
first = next(n for n in tree.body if nm(n) == sys.argv[1]); last = next(n for n in tree.body if nm(n) == sys.argv[2])
a = min([first.lineno] + [d.lineno for d in getattr(first, 'decorator_list', [])])
while a - 2 >= 0 and L[a - 2].startswith('#'): a -= 1
print(a, last.end_lineno)
