#!/usr/bin/env python3
"""Verify cached independent agency cutouts against their recorded SHA256."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for site in ['B11','B12','V11','V15','B12_wide']:
 provenance=json.loads((ROOT/'data/provenance'/(site+'.json')).read_text())
 failed=provenance['failed_scenes']
 if failed:raise RuntimeError(f'{site}: {len(failed)} provider downloads incomplete')
 for record in provenance['successful_scenes']:
  path=ROOT/'data/raw'/site/record['file'];h=hashlib.sha256()
  with path.open('rb') as f:
   for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
  if h.hexdigest()!=record['sha256']:raise RuntimeError('Raw input hash mismatch: '+str(path))
 print(site,len(provenance['successful_scenes']),'cached input hashes verified',flush=True)
