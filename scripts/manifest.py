#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files={}
for folder in ['src','config','scripts','docs','guidance','figures','data/results','data/saved_outputs','data/provenance','data/manifests','data/reconnaissance','report']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.name != 'artifact_sha256.json' and p.suffix not in ['.aux','.log','.out','.fls','.toc','.fdb_latexmk']:
   files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['CMakeLists.txt','AGENTS.md','README.md','rebuild.sh','requirements.txt','.gitignore','.gitattributes']:
 p=ROOT/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
for folder in ['data/derived','data/geography']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and 'tiles' not in p.parts and p.suffix not in ['.f32','.u16','.u8']:
   files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT/'data/results/artifact_sha256.json').write_text(json.dumps(files,indent=2,sort_keys=True)+'\n')
print('Hashed',len(files),'project artifacts')
