#!/usr/bin/env python3
"""Build the panel audit and report tables from saved outputs and declared scope."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report'
def read(path):
 with path.open() as f:return list(csv.DictReader(f))
def tex(s):
 return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}'}.get(c,c) for c in str(s))
def code(s):
 return r'\texttt{'+tex(s).replace('/',r'/\allowbreak{}')+'}'
def main():
 OUT.mkdir(exist_ok=True)
 data=ROOT/'data/results';records=[]
 stats='build/avulsion statistics config/sites.csv config/channel_measurements.csv data/derived data/results'
 def add(panel,quantity,status,spec,parameters,command,plot,limitation):
  records.append(dict(panel=panel,quantity=quantity,status=status,documentation=spec,parameters=parameters,data_command=command,plot_command='.runtime/py311/bin/python scripts/plot.py --figure '+plot,limitation=limitation))
 for panel,region in zip(['1a','1b','1c','1d'],['Northern Andes (16)','Central Andes (14)','Himalaya (6)','New Guinea (27)']):
  add(panel,'Site distribution: '+region,'independently reproduced','Main Fig. 1 caption; permitted site coordinates','63 coordinates overall; independent zoom-7 terrain resampled to 600 x 800; B15 included',
      'build/avulsion catalog config/sites.csv data/results; .runtime/py311/bin/python scripts/terrain.py','fig1',
      'Reproduces the geographic site distribution, not pixel-identical cartography. Background source, map bounds and label placement differ. This is an observational map, not a model result.')
 add('1 locator','Global study-region locations','partially reproduced','Main Fig. 1','Same coordinates; rectangular longitude/latitude axes',
     'build/avulsion catalog config/sites.csv data/results','fig1','Global positions generated independently; continental outline and original inset design absent.')
 for panel,quantity in [('2a','Cumulative B12 disturbance footprint'),('2b','Detail of B12 disturbance footprint')]:
  add(panel,quantity,'partially reproduced' if (ROOT/'config/annotations/B12_wide/polygons.csv').exists() else 'not reproduced',
      'Main Fig. 2 caption; Methods fingerprinting; Supplementary Table 2','30 m; B90/G50 and W75/G50; independent rectangular domain and manual polygon if available',
      'build/avulsion analyze data/raw/B12_wide data/derived/B12_wide; build/avulsion measure data/derived/B12_wide config/annotations/B12_wide/polygons.csv data/derived/B12_wide/event',
      'fig2','Published spatial pattern and parent/new-channel relationship are not recovered. This is a partial spectral-method attempt, not a verified reconstruction of the published event. See docs/published-comparison.md.')
 for i,year in enumerate([2011,2013,2015,2017],1):
  add(f'2c upper {i}','High-resolution validation observation','not reproduced','Main Fig. 2 caption','WorldView imagery; published dates recorded only for post hoc comparison',
      'No data command: independently licensed validation image unavailable','fig2','An explicit absence notice occupies this slot. No copied validation image is displayed.')
  add(f'2c lower {i}',f'Annual B12 detection counterpart (attempt year {year})','partially reproduced' if (ROOT/'config/annotations/B12_wide/polygons.csv').exists() else 'not reproduced',
      'Main Fig. 2 caption; Methods; Supplementary Table 2','30 m annual median; selected signature; four attempt years are independently declared',
      'build/avulsion analyze data/raw/B12_wide data/derived/B12_wide; build/avulsion measure data/derived/B12_wide config/annotations/B12_wide/polygons.csv data/derived/B12_wide/event',
      'fig2','Published annual counterparts are 2007, 2010, 2013, 2017, identified only during post hoc assessment; our declared years remain unchanged. High-resolution counterparts unavailable; no pixel agreement score can be computed.')
 for panel,quantity in [('3a','Style ratio versus distance / width'),('3b','Style ratio versus channel-belt slope'),('4','Style-ratio distributions by morphology'),('S3a','Slope distributions by morphology'),('S3b','Distance / width distributions by morphology')]:
  add(panel,quantity,'not reproduced','Main Figs. 3, 4; Supplementary Fig. 3; Methods channel measurements',
      'D/w; elevation drop / reach length; three morphology classes; D/w > 60 fit subset; range whiskers',stats,
      'fig3' if panel.startswith('3') else 'fig4' if panel=='4' else 'supp3',
      'No complete independent event-plus-channel-geometry record exists. All 63 sites are audited; empty results stay empty. Statistical arithmetic is tested on analytical fixtures, which are not plotted as study data.')
 add('5a','Sarare regional river context','partially reproduced','Main Fig. 5 caption','V11 and V15 permitted coordinates',
     'build/avulsion catalog config/sites.csv data/results','fig5','Location plot only; full river-context satellite mosaic and a traced connecting channel are absent.')
 for site,context,foot in [('V15','5b','5c'),('V11','5d','5e')]:
  add(context,site+' satellite context','partially reproduced','Main Fig. 5 caption; Methods annual composites',
      'Independent 2017 annual median; 30 m; QA screen; fixed display stretch',
      f'build/avulsion analyze data/raw/{site} data/derived/{site}','fig5','Paper uses 2019 Google Earth context; our independent 2017 Landsat observation has different timing and resolution.')
  add(foot,site+' disturbance footprint','partially reproduced' if site=='V11' else 'not reproduced','Main Fig. 5 caption; Methods fingerprinting',
      'V11: parent 1986; event observation 1996--1998; partial manual mask; selected signature' if site=='V11' else '30 m annual candidates; event not uniquely identified',
      f'build/avulsion analyze data/raw/{site} data/derived/{site}'+(f'; build/avulsion measure data/derived/{site} config/annotations/{site}/polygons.csv data/derived/{site}/event' if site=='V11' else ''),
      'fig5','V11 has unequal windows and disturbance crossing the domain edge; its diagnostic ratio is not a full-event style estimate.' if site=='V11' else 'Braided-channel migration and a specific avulsion could not be distinguished confidently from these observations; no event polygon was invented.')
 for panel,year in zip(['S1a','S1b','S1c','S1d'],[1995,2011,2013,2015]):
  add(panel,f'B12 land surface in {year}','partially reproduced','Supplementary Fig. 1 caption; Methods annual compositing',
      f'{year}; 30 m; independent Collection 2 annual RGB; fixed reflectance / 0.35 display stretch and gamma 1/1.6',
      'build/avulsion analyze data/raw/B12_wide data/derived/B12_wide','supp1','Same named site and years; independently chosen domain, different processing and no verified match to original image footprint.')
 for panel in ['S2a','S2b']:
  add(panel,'B11 fingerprint'+(' detail' if panel=='S2b' else ''),'not reproduced','Supplementary Fig. 2; Methods fingerprinting',
      '30 m; 1986--2017 archive; both published spectral signatures',
      'build/avulsion analyze data/raw/B11 data/derived/B11','supp2','Annual composites and candidate masks were generated, but a unique complete event mask and timing were not established.')
 add('S2c','B11 high-resolution validation image','not reproduced','Supplementary Fig. 2 caption','WorldView observation dated 8 July 2016',
     'No data command: independently licensed validation image unavailable','supp2','No validation image or copied manuscript panel is substituted.')
 with (data/'panel_record.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
 blocks=[]
 for row in records:
  blocks.append(r'\subsubsection*{Panel '+tex(row['panel'])+' --- '+tex(row['status'])+'}\n'+
    tex(row['quantity'])+'. '+tex(row['documentation'])+'.\n\n'+
    r'\textit{Parameters:} '+tex(row['parameters'])+'.\n\n'+
    r'\textit{Data:} '+code(row['data_command'])+'.\n\n'+
    r'\textit{Plot:} '+code(row['plot_command'])+'.\n\n'+tex(row['limitation'])+'\n')
 (OUT/'panel_ledger.tex').write_text('\n'.join(blocks))
 table=[r'\begin{tabular}{lrrrrr}\toprule',r'Domain & Scenes & Years & Min. coverage & Median coverage & Max. coverage\\\midrule']
 for site in ['B11','B12','V11','V15','B12_wide']:
  annual=read(ROOT/'data/derived'/site/'annual.csv')
  cov=sorted(int(x['valid_pixels'])/int(x['total_pixels']) for x in annual)
  m=len(cov);med=(cov[(m-1)//2]+cov[m//2])/2
  prov=json.loads((ROOT/'data/provenance'/(site+'.json')).read_text())
  table.append(f"{tex(site)} & {len(prov['successful_scenes'])} & {len(annual)} & {min(cov):.3f} & {med:.3f} & {max(cov):.3f} "+r'\\')
 table.append(r'\bottomrule\end{tabular}')
 (OUT/'coverage_table.tex').write_text('\n'.join(table))
 tests=[]
 for name in ['validation','integration_checks','real_checks']:
  r=read(data/(name+'.csv'));passed=sum(x['pass'] in ['1','True'] for x in r)
  tests.append((name,len(r),passed))
 (OUT/'test_table.tex').write_text(r'\begin{tabular}{lrr}\toprule Check suite & Checks & Passed\\\midrule'+'\n'+'\n'.join(f'{tex(n)} & {c} & {p} '+r'\\' for n,c,p in tests)+'\n'+r'\bottomrule\end{tabular}')
 # These are computed outputs, never comparison targets used by the pipeline.
 v=read(ROOT/'data/derived/V11/event/measurements.csv')
 text=r'\begin{tabular}{lrrr}\toprule Signature & Parent area (km$^2$) & Partial event area (km$^2$) & Area ratio\\\midrule'+'\n'
 for r in v:text+=f"{r['signature']} & {float(r['parent_area_m2'])/1e6:.4f} & {float(r['avulsion_area_m2'])/1e6:.4f} & {float(r['SR']):.4f} "+r'\\'+'\n'
 (OUT/'v11_table.tex').write_text(text+r'\bottomrule\end{tabular}')
 v=read(ROOT/'data/derived/B12_wide/event/measurements.csv')
 text=r'\begin{tabular}{lrrr}\toprule Signature & Parent area (km$^2$) & Partial event area (km$^2$) & Area ratio\\\midrule'+'\n'
 for r in v:text+=f"{r['signature']} & {float(r['parent_area_m2'])/1e6:.4f} & {float(r['avulsion_area_m2'])/1e6:.4f} & {float(r['SR']):.4f} "+r'\\'+'\n'
 (OUT/'b12_table.tex').write_text(text+r'\bottomrule\end{tabular}')
 if (data/'domain_sensitivity.csv').exists():
  r=read(data/'domain_sensitivity.csv')
  text=r'\begin{tabular}{lrrrr}\toprule Year & Signature & Intersection/union & Pixel agreement & Mean RGB difference\\\midrule'+'\n'
  for x in r:
   text+=f"{x['year']} & {x['signature']} & {float(x['IoU']):.3f} & {float(x['agreement']):.3f} & {float(x['mean_abs_RGB_difference']):.4g} "+r'\\'+'\n'
  (OUT/'domain_table.tex').write_text(text+r'\bottomrule\end{tabular}')
 counts={s:sum(r['status']==s for r in records) for s in ['independently reproduced','partially reproduced','not reproduced']}
 (data/'report_summary.json').write_text(json.dumps({'panel_status_counts':counts,'validation':tests,'scope_note':'Four events acquired; one additional B12 domain. Complete statistical event records: zero.'},indent=2)+'\n')
 print('Recorded',len(records),'panel slots:',counts)
if __name__=='__main__':main()
