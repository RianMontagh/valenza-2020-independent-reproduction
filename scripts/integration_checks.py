#!/usr/bin/env python3
"""Independent end-to-end checks with tiny, explicitly synthetic inputs.

These arrays verify numerical operations. They are never manuscript data.
"""
import csv
import os
from pathlib import Path
import subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def main():
 base=ROOT/'.runtime/integration'
 inp=base/'input';out=base/'output';inp.mkdir(parents=True,exist_ok=True)
 (inp/'grid.txt').write_text('3 1 30 -30 0 0 32619\n')
 # Two scenes: reflectances at pixels are 0.075, 0.35, and missing.
 # QA removes a third highly bright observation from the annual median.
 for i in range(3):
  a=np.zeros((8,1,3),dtype='<u2');a[:6,0,0]=10000;a[:6,0,1]=20000
  a[6,0,:2]=64
  if i==2:a[:6,0,0]=50000;a[6,0,0]=8
  a.tofile(inp/f'{i}.u16')
 with (inp/'scenes.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['date','sensor','file'])
  for i in range(3):w.writerow([f'2000-01-0{i+1}',5,f'{i}.u16'])
 env=dict(os.environ,OMP_NUM_THREADS='2')
 subprocess.run([str(ROOT/'build/avulsion'),'analyze',str(inp),str(out)],check=True,env=env,stdout=subprocess.DEVNULL)
 tc=np.fromfile(out/'2000_tct.f32',dtype='<f4').reshape(3,3)
 rgb=np.fromfile(out/'2000_rgb.f32',dtype='<f4').reshape(3,3)
 # Constants are independently summed from the written coefficient table.
 expected=np.array([2.1920,-.4104,-.0471])*.075
 checks=[('cloud_does_not_contaminate_median',bool(np.allclose(rgb[:,0],.075,atol=1e-7))),
         ('known_uniform_spectrum',bool(np.allclose(tc[:,0],expected,atol=1e-7))),
         ('missing_pixel_stays_missing',bool(np.isnan(tc[:,2]).all())),
         ('bright_pixel_detected',np.fromfile(out/'2000_B.u8',dtype='u1').tolist()==[0,1,0]),
         ('wet_pixel_detected',np.fromfile(out/'2000_W.u8',dtype='u1').tolist()==[0,0,0])]
 # Polygon areas and temporal union through the actual measurement CLI.
 ann=base/'annotations';ann.mkdir(exist_ok=True)
 (ann/'polygons.csv').write_text('role,x_pixel,y_pixel\nparent,1,0\nparent,2,0\nparent,2,1\nparent,1,1\navulsion,1,0\navulsion,2,0\navulsion,2,1\navulsion,1,1\n')
 (ann/'years.txt').write_text('2000 2000 2000 2000\n')
 subprocess.run([str(ROOT/'build/avulsion'),'measure',str(out),str(ann/'polygons.csv'),str(base/'measure')],check=True,env=env)
 m=list(csv.DictReader((base/'measure/measurements.csv').open()))
 checks.append(('known_pixel_area_900_m2',float(m[0]['avulsion_area_m2'])==900))
 checks.append(('identical_real_masks_SR1',float(m[0]['SR'])==1))
 # Analytical power law S_R=(D/w / 100)^2, three independently constructed
 # validation points. These files stay under .runtime, away from study data.
 (base/'sites.csv').write_text('site_id,latitude,longitude\nV1,0,0\nV2,0,0\nV3,0,0\n')
 (base/'channels.csv').write_text('site,width,distance,zu,zd,length,type,provenance\nV1,10,1000,10,0,10000,1,synthetic_check\nV2,10,2000,10,0,10000,1,synthetic_check\nV3,10,4000,10,0,10000,1,synthetic_check\n')
 for site,value in [('V1',1),('V2',4),('V3',16)]:
  ep=base/'derived'/site/'event';ep.mkdir(parents=True,exist_ok=True)
  (ep/'selected.txt').write_text(f'B {value}\n')
 subprocess.run([str(ROOT/'build/avulsion'),'statistics',str(base/'sites.csv'),str(base/'channels.csv'),str(base/'derived'),str(base/'stats')],check=True,env=env)
 fit=list(csv.DictReader((base/'stats/regression.csv').open()))[0]
 group=list(csv.DictReader((base/'stats/morphology_summary.csv').open()))[0]
 checks.extend([('analytical_power_law_exponent',abs(float(fit['slope_log10'])-2)<1e-9),
                ('analytical_power_law_r_squared',abs(float(fit['r_squared'])-1)<1e-9),
                ('known_group_median',float(group['median'])==4),
                ('known_group_range',float(group['min'])==1 and float(group['max'])==16)])
 # Shift the grid origin one pixel west and north, pad known observations,
 # then verify that geographic overlap excludes the padding and missing cell.
 large=base/'large';large.mkdir(exist_ok=True)
 (large/'grid.txt').write_text('5 3 30 -30 -30 30 32619\n')
 (large/'annual.csv').write_text((out/'annual.csv').read_text())
 padded=np.full((3,3,5),np.nan,dtype='<f4');padded[:,1,1:4]=rgb
 padded.tofile(large/'2000_rgb.f32')
 for mode in ['B','W']:
  padded=np.zeros((3,5),dtype='u1');padded[1,1:4]=np.fromfile(out/f'2000_{mode}.u8',dtype='u1')
  padded.tofile(large/f'2000_{mode}.u8')
 subprocess.run([str(ROOT/'build/avulsion'),'compare-domains',str(out),str(large),str(base/'comparison.csv')],check=True,env=env)
 comp=list(csv.DictReader((base/'comparison.csv').open()))
 checks.extend([('translated_overlap_foreground_IoU',float(comp[0]['IoU'])==1),
                ('translated_overlap_valid_count',int(comp[0]['common_valid'])==2),
                ('translated_overlap_spectrum_unchanged',float(comp[0]['mean_abs_RGB_difference'])==0)])
 path=ROOT/'data/results/integration_checks.csv';path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w') as f:
  w=csv.writer(f);w.writerow(['test','pass']);w.writerows(checks)
 for name,ok in checks:print(name,'PASS' if ok else 'FAIL')
 if not all(x[1] for x in checks):raise SystemExit(1)
if __name__=='__main__':main()
