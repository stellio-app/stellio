"""Génère une fausse bibliothèque (STL minuscules) pour tester Stellio à grande échelle.
Usage : python3 tools/gen_library.py /chemin/vers/dossier 50000   — puis ajoutez ce dossier comme source."""
import os, struct, random, sys
root=sys.argv[1]; n=int(sys.argv[2])
random.seed(1)
def stl(path,s):
    tris=[((0,0,0),(s,0,0),(0,s,0)),((0,0,0),(0,s,0),(0,0,s)),((0,0,0),(0,0,s),(s,0,0)),((s,0,0),(0,0,s),(0,s,0))]
    with open(path,'wb') as f:
        f.write(b'\0'*80); f.write(struct.pack('<I',len(tris)))
        for t in tris:
            f.write(struct.pack('<3f',0,0,0))
            for v in t: f.write(struct.pack('<3f',*v))
            f.write(b'\0\0')
cats=['Figurines','Mecanique','Deco','Outils','Jeux','Cosplay','Maison','Auto']
for i in range(n):
    d=os.path.join(root,random.choice(cats),f"pack{i//250:03d}")
    os.makedirs(d,exist_ok=True)
    stl(os.path.join(d,f"modele_{i:05d}_{random.choice(['dragon','vase','support','boite','engrenage','clip'])}.stl"),random.randint(5,80))
print('ok')
