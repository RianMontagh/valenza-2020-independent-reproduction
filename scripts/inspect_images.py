#!/usr/bin/env python3
"""Display saved C++ composites for independent annotation; no classification."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=ROOT/'data/derived'

def grid(site):
 vals=(BASE/site/'grid.txt').read_text().split()
 return int(vals[0]),int(vals[1])
def rgb(site,year):
 w,h=grid(site)
 p=BASE/site/f'{year}_rgb.f32'
 if not p.exists():return None
 a=np.fromfile(p,dtype='<f4').reshape(3,h,w).transpose(1,2,0)
 # Fixed display stretch only; it never changes classified pixels.
 return np.nan_to_num(np.clip(a/0.35,0,1)**(1/1.6),nan=.6)
def main():
 global BASE
 p=argparse.ArgumentParser();p.add_argument('site');p.add_argument('--years',default='1986,1990,1995,2000,2005,2010,2011,2013,2015,2017');p.add_argument('--input-root',default='data/derived');p.add_argument('--crop');args=p.parse_args()
 BASE=ROOT/args.input_root
 years=[int(x) for x in args.years.split(',')]
 fig,axs=plt.subplots((len(years)+3)//4,4,figsize=(16,4*((len(years)+3)//4)),squeeze=False)
 for ax,year in zip(axs.flat,years):
  a=rgb(args.site,year)
  if a is not None:
   if args.crop:
    x0,x1,y0,y1=map(int,args.crop.split(','));ax.imshow(a[y0:y1,x0:x1],extent=[x0,x1,y1,y0])
   else:ax.imshow(a)
  else:ax.text(.5,.5,'No acquired year',ha='center',transform=ax.transAxes)
  ax.set_title(str(year));ax.set_xlabel('pixel column');ax.set_ylabel('pixel row')
 for ax in list(axs.flat)[len(years):]:ax.axis('off')
 fig.suptitle(args.site+' — independent Landsat composites for inspection');fig.tight_layout()
 out=ROOT/'figures/inspection';out.mkdir(parents=True,exist_ok=True)
 fig.savefig(out/(args.site+'.png'),dpi=120);plt.close(fig)
if __name__=='__main__':main()
