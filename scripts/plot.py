#!/usr/bin/env python3
"""All manuscript-style plots are drawn from saved independent analysis output.

No manuscript image, digitized curve or author plotting script is accessed.
"""
import argparse
import csv
import json
import os
import textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.dpi':180,'pdf.fonttype':42})
OUT=ROOT/'figures'
DERIVED=ROOT/'data/derived'
SITES=['B11','B12','V11','V15']

def rows(path):
 if not path.exists():return []
 with path.open() as f:return list(csv.DictReader(f))

def grid(site):
 p=DERIVED/site/'grid.txt'
 v=p.read_text().split()
 return int(v[0]),int(v[1]),float(v[2]),float(v[3]),float(v[4]),float(v[5])

def raster(site,filename,bands=1,dtype='<f4'):
 p=DERIVED/site/filename
 w,h,*_=grid(site)
 if not p.exists():return None
 return np.fromfile(p,dtype=dtype).reshape((bands,h,w)) if bands>1 else np.fromfile(p,dtype=dtype).reshape(h,w)

def extent(site):
 w,h,dx,dy,*_=grid(site)
 return [0,w*dx/1000,h*(-dy)/1000,0]

def show_rgb(ax,site,year,title):
 a=raster(site,f'{year}_rgb.f32',3)
 if a is None:
  missing(ax,'No independently acquired composite for this year');return
 a=np.moveaxis(a,0,-1)
 valid=np.all(np.isfinite(a),axis=-1)
 image=np.clip(np.nan_to_num(a)/.35,0,1)**(1/1.6)
 image[~valid]=.75
 ax.imshow(image,extent=extent(site));ax.set_title(title);ax.set_xlabel('Easting from domain edge (km)');ax.set_ylabel('Distance south (km)')

def missing(ax,message):
 width=max(22,int(ax.get_position().width*ax.figure.get_figwidth()*10))
 wrapped='\n'.join(textwrap.fill(line,width=width) for line in message.split('\n'))
 ax.axis('off');ax.text(.5,.5,'NOT REPRODUCED\n\n'+wrapped,ha='center',va='center',transform=ax.transAxes,color='#803333',fontsize=8)

def finish(fig,name):
 OUT.mkdir(exist_ok=True)
 fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
 fig.savefig(OUT/(name+'.png'),bbox_inches='tight')
 plt.close(fig)

def map_panel(ax,locations,region,title):
 terrain=ROOT/'data/geography'/f'{region}.npz'
 if terrain.exists():
  with np.load(terrain) as d:
   lo,la,hi,ha=d['bbox'];image=ax.imshow(d['elevation'],extent=[lo,hi,la,ha],vmin=0,vmax=5000,cmap='Greys',origin='upper',aspect='auto')
 else:image=None
 selected=[r for r in locations if r['region']==region]
 for row in selected:
  lon,lat=float(row['longitude_deg']),float(row['latitude_deg'])
  ax.scatter(lon,lat,s=13,facecolor='#d69a27',edgecolor='black',linewidth=.35,zorder=3)
  ax.annotate(row['site_id'],(lon,lat),xytext=(3,2),textcoords='offset points',fontsize=5,zorder=4)
 ax.set_title(f'{title} ({len(selected)} events)');ax.set_xlabel('Longitude (degrees)');ax.set_ylabel('Latitude (degrees)')
 return image

def fig1():
 locations=rows(ROOT/'data/results/site_locations.csv')
 fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained')
 for ax,region,title in zip(axs.flat,['andes_north','andes_central','himalaya','new_guinea'],
                          ['(a) Northern Andes','(b) Central Andes','(c) Himalaya','(d) New Guinea']):
  im=map_panel(ax,locations,region,title)
 if im:fig.colorbar(im,ax=axs.ravel().tolist(),label='Independent terrain elevation (m)',shrink=.5)
 fig.suptitle('Figure 1 — site locations reconstructed from permitted metadata\nIndependent terrain backdrop; B15 is included here')
 finish(fig,'fig1')
 # A separately generated geographic locator, not a model result.
 fig,ax=plt.subplots(figsize=(8,3.2));ax.scatter([float(r['longitude_deg']) for r in locations],[float(r['latitude_deg']) for r in locations],s=8)
 ax.set(xlim=(-180,180),ylim=(-60,70),xlabel='Longitude (degrees)',ylabel='Latitude (degrees)',title='Figure 1 locator — study locations on global coordinates');ax.grid(alpha=.25)
 finish(fig,'fig1_locator')

def footprint(ax,site,mode=None,crop=None,event=True):
 if mode is None:
  selected=DERIVED/site/'event/selected.txt'
  mode=selected.read_text().split()[0] if event and selected.exists() else 'W'
 filename=f'event/fingerprint_{mode}.u16' if event else f'candidate_years_{mode}.u16'
 arr=raster(site,filename,dtype='<u2')
 if arr is None:
  missing(ax,'An independently validated channel mask and event window are unavailable.');return None
 extent_=extent(site)
 vmax_=max(2,int(arr.max()))
 if crop:
  x0,x1,y0,y1=crop;arr=arr[y0:y1,x0:x1];dx=grid(site)[2]/1000;extent_=[x0*dx,x1*dx,y1*dx,y0*dx]
 shown=np.ma.masked_equal(arr,0)
 image=ax.imshow(shown,extent=extent_,cmap='viridis',vmin=1,vmax=vmax_)
 ax.set_facecolor('#f3f3f3');ax.set_xlabel('Easting from domain edge (km)');ax.set_ylabel('Distance south (km)')
 return image

def fig2():
 fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
 for ax,title,crop in zip(axs,['(a) B12: partial central-reach footprint','(b) Independently selected detail'],[(300,1000,1200,1800),(590,840,1450,1650)]):
  im=footprint(ax,'B12_wide',crop=crop)
  ax.set_title(title)
  if im is not None:fig.colorbar(im,ax=ax,label='Number of retained activity years',shrink=.75)
 fig.suptitle('Figure 2a,b attempt — independent masks and imagery; partial reproduction')
 finish(fig,'fig2ab')
 fig,axs=plt.subplots(2,4,figsize=(12,6),layout='constrained',gridspec_kw={'height_ratios':[1,2]})
 for col,year in enumerate([2011,2013,2015,2017]):
  missing(axs[0,col],'Independent WorldView validation image not acquired.');axs[0,col].set_title(f'(c) Validation slot {col+1}')
  selected=DERIVED/'B12_wide/event/selected.txt'
  mode=selected.read_text().split()[0] if selected.exists() else 'W'
  arr=raster('B12_wide',f'{year}_{mode}.u8',dtype='u1')
  mask=raster('B12_wide','event/avulsion_mask.u8',dtype='u1')
  if arr is not None and mask is not None:
   shown=np.ma.masked_where((arr*mask)==0,arr)[1450:1650,590:840]
   axs[1,col].imshow(shown,extent=[590*.03,840*.03,1650*.03,1450*.03],cmap='Blues',vmin=0,vmax=1)
   axs[1,col].set_xlabel('Easting (km)')
   if col==0:axs[1,col].set_ylabel('Distance south (km)')
   axs[1,col].set_title(f'{year}: annual detections')
  else:missing(axs[1,col],'Independent event mask is unavailable.')
 fig.suptitle('Figure 2c attempt — independent annual detections; validation images unavailable\nAttempt dates and image extent differ from the published counterparts')
 finish(fig,'fig2c')

def relationships(which):
 data=rows(ROOT/'data/results/relationships.csv')
 if which=='fig3':
  fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
  for ax,xkey,label in zip(axs,['normalized_distance','slope'],['Distance / channel width','Channel-belt slope (m/m)']):
   if data:
    ax.scatter([float(r[xkey]) for r in data],[float(r['SR']) for r in data]);ax.set(xscale='log',yscale='log',xlabel=label,ylabel='Avulsion style ratio')
   else:missing(ax,'Independent channel widths, mountain-front centerlines, slopes and validated event ratios are missing.\nPublished measurements are excluded.')
  fig.suptitle('Figure 3a,b — reproduction attempt, no substituted measurements');finish(fig,which)
 elif which=='fig4':
  fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
  summary=rows(ROOT/'data/results/morphology_summary.csv')
  if summary:
   ax.bxp([{'label':r['morphology'],'med':float(r['median']),'q1':float(r['q25']),'q3':float(r['q75']),'whislo':float(r['min']),'whishi':float(r['max']),'fliers':[]} for r in summary],showfliers=False)
   ax.set_yscale('log');ax.set_ylabel('Avulsion style ratio')
  else:missing(ax,'The independently measured morphology / ratio sample is incomplete.\nNo published boxplot statistics are used.')
  ax.set_title('Figure 4 — morphology distributions not reproduced');finish(fig,which)
 else:
  fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
  for ax,quantity in zip(axs,['slope','normalized_distance']):
   if data:
    groups=[];labels=[]
    for typ in ['1','2','3']:
     v=[float(r[quantity]) for r in data if r['morphology']==typ]
     if v:groups.append(v);labels.append(typ)
    ax.boxplot(groups,tick_labels=labels,whis=(0,100));ax.set_ylabel(quantity)
   else:missing(ax,'Independent channel geometry and morphology records are missing.')
  fig.suptitle('Supplementary Figure 3a,b — not reproduced');finish(fig,'supp3')

def fig5():
 fig,ax=plt.subplots(figsize=(9,3),layout='constrained')
 data=rows(ROOT/'data/results/site_locations.csv');selected=[r for r in data if r['site_id'] in ['V11','V15']]
 for r in selected:
  ax.scatter(float(r['longitude_deg']),float(r['latitude_deg']),s=40);ax.annotate(r['site_id'],(float(r['longitude_deg']),float(r['latitude_deg'])),xytext=(6,5),textcoords='offset points')
 ax.set(xlabel='Longitude (degrees)',ylabel='Latitude (degrees)',title='Figure 5a — independent location plot; full river-context image unavailable')
 finish(fig,'fig5a')
 fig,axs=plt.subplots(2,2,figsize=(10,9),layout='constrained')
 for col,site in enumerate(['V15','V11']):
  show_rgb(axs[0,col],site,2017,f'({"b" if col==0 else "d"}) {site}: independent 2017 annual composite')
  im=footprint(axs[1,col],site)
  axs[1,col].set_title(f'({"c" if col==0 else "e"}) {site}: '+('partial 1996–1998 footprint' if site=='V11' else 'footprint not identified'))
  if im is not None:fig.colorbar(im,ax=axs[1,col],label='Activity years',shrink=.7)
 fig.suptitle('Figure 5b–e attempts — independently processed observations, partial reproduction')
 finish(fig,'fig5bcde')

def supp1():
 fig,axs=plt.subplots(2,2,figsize=(10,9),layout='constrained')
 for ax,year,letter in zip(axs.flat,[1995,2011,2013,2015],['a','b','c','d']):
  show_rgb(ax,'B12_wide',year,f'({letter}) {year}: independently generated annual RGB')
 fig.suptitle('Supplementary Figure 1 attempt — B12 land-surface evolution\n30 m Collection 2 observations; display stretch is fixed across years')
 finish(fig,'supp1')

def supp2():
 fig,axs=plt.subplots(1,3,figsize=(13,4),layout='constrained')
 im=footprint(axs[0],'B11');axs[0].set_title('(a) B11 independent footprint attempt')
 if im is not None:fig.colorbar(im,ax=axs[0],label='Activity years',shrink=.7)
 im=footprint(axs[1],'B11',crop=(180,440,250,550));axs[1].set_title('(b) Independently selected detail')
 missing(axs[2],'WorldView validation image of 8 July 2016 was not acquired.');axs[2].set_title('(c) Validation observation')
 fig.suptitle('Supplementary Figure 2 attempt');finish(fig,'supp2')

def diagnostics():
 fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
 for ax,site in zip(axs.flat,SITES):
  r=rows(DERIVED/site/'annual.csv')
  if not r:missing(ax,'No annual output');continue
  years=[int(x['year']) for x in r];coverage=[float(x['valid_pixels'])/float(x['total_pixels']) for x in r]
  ax.plot(years,coverage,'o-',ms=3);ax.set(ylim=(0,1.05),xlabel='Year',ylabel='Fraction with valid reflectance',title=site);ax.grid(alpha=.2)
 fig.suptitle('Coverage audit of independently computed annual composites');finish(fig,'coverage')
 fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained')
 for ax,site in zip(axs.flat,SITES):
  im=footprint(ax,site,event=False);ax.set_title(site+' — unmasked candidate detections')
  if im is not None:fig.colorbar(im,ax=ax,label='Detection years',shrink=.65)
 fig.suptitle('Diagnostic only: candidate pixels include pre-existing channels and unrelated disturbance\nThese maps are not avulsion fingerprints or reproduced manuscript results')
 finish(fig,'candidate_diagnostics')

def main():
 p=argparse.ArgumentParser();p.add_argument('--figure',default='all');args=p.parse_args()
 calls={'fig1':fig1,'fig2':fig2,'fig3':lambda:relationships('fig3'),'fig4':lambda:relationships('fig4'),'fig5':fig5,'supp1':supp1,'supp2':supp2,'supp3':lambda:relationships('supp3'),'diagnostics':diagnostics}
 if args.figure=='all':
  for fn in calls.values():fn()
 else:calls[args.figure]()
if __name__=='__main__':main()
