#!/usr/bin/env python3
"""Losslessly package independently generated arrays for archiving.

The files contain outputs of C++ analysis. This script performs no analysis.
"""
from pathlib import Path
import argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
TYPES={'.f32':'<f4','.u16':'<u2','.u8':'u1'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--unpack',action='store_true');args=p.parse_args()
 archive=ROOT/'data/saved_outputs';archive.mkdir(parents=True,exist_ok=True)
 if args.unpack:
  for file in archive.glob('*/*.npz'):
   with np.load(file) as d:
    for key in d.files:
     out=ROOT/'data/derived'/file.parent.name/key
     out.parent.mkdir(parents=True,exist_ok=True);d[key].tofile(out)
  return
 for site in (ROOT/'data/derived').iterdir():
  if not site.is_dir():continue
  batches={}
  for file in site.rglob('*'):
   if file.suffix in TYPES:
    # Split large domains by individual array: every file stays below GitHub's
    # 100 MB limit, without lossy compression or dropping generated data.
    key=str(file.relative_to(site))
    batches[key.replace('/','__')]={key:np.fromfile(file,dtype=TYPES[file.suffix])}
  target=archive/site.name;target.mkdir(parents=True,exist_ok=True)
  for name,arrays in batches.items():
   file=target/(name+'.npz');np.savez_compressed(file,**arrays)
   with np.load(file) as saved:
    for name,a in arrays.items():
     if not np.array_equal(a,saved[name],equal_nan=True):raise RuntimeError('Archive round-trip failed')
   print('Saved losslessly',file.relative_to(ROOT),file.stat().st_size,flush=True)
if __name__=='__main__':main()
