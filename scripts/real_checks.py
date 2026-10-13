#!/usr/bin/env python3
"""Audit saved C++ outputs using bounds that follow from their definitions."""
import csv
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def main():
 checks=[]
 for site in ['B11','B12','V11','V15','B12_wide']:
  p=ROOT/'data/derived'/site
  if not (p/'annual.csv').exists():continue
  with (p/'annual.csv').open() as f:rows=list(csv.DictReader(f))
  for r in rows:
   valid=int(r['valid_pixels']);n=int(r['total_pixels']);b=int(r['bright_pixels']);w=int(r['wet_pixels'])
   checks.extend([(site,r['year'],'valid_pixel_bound',0<=valid<=n),
                  (site,r['year'],'B90_area_bound',b<=int(np.ceil(.10*valid))),
                  (site,r['year'],'W75_area_bound',w<=int(np.ceil(.25*valid)))])
  cov=np.fromfile(p/'coverage_years.u16',dtype='<u2')
  for mode in ['B','W']:
   counts=np.fromfile(p/f'candidate_years_{mode}.u16',dtype='<u2')
   checks.append((site,'all',f'{mode}_counts_bounded_by_coverage',bool(np.all(counts<=cov))))
   expected=np.zeros_like(counts)
   for r in rows:expected+=np.fromfile(p/f"{r['year']}_{mode}.u8",dtype='u1')
   checks.append((site,'all',f'{mode}_sum_matches_annual_masks',bool(np.array_equal(counts,expected))))
 out=ROOT/'data/results/real_checks.csv'
 with out.open('w') as f:
  writer=csv.writer(f);writer.writerow(['site','year','check','pass']);writer.writerows(checks)
 failed=[r for r in checks if not r[-1]]
 print(f'{len(checks)} real-data consistency checks; {len(failed)} failures')
 if failed:raise SystemExit(1)
if __name__=='__main__':main()
