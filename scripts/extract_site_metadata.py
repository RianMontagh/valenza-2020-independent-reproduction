#!/usr/bin/env python3
"""Optional audit of the sole permitted author-data exception: IDs and locations.

The XLSX is held only in memory. Only cells in columns A, B, and C of the
first worksheet are parsed into records. No event dates or measurements are
read or retained. This is not called by the rebuild, which uses sites.csv.
"""
import csv
import io
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import requests
ROOT=Path(__file__).resolve().parents[1]
URL='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-020-15859-9/MediaObjects/41467_2020_15859_MOESM3_ESM.xlsx'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def main():
 response=requests.get(URL,timeout=120);response.raise_for_status()
 with zipfile.ZipFile(io.BytesIO(response.content)) as book:
  # Shared strings are retrieved lazily by referenced index; no unrelated
  # worksheet cells, labels, or scientific outcomes are displayed.
  strings=ET.fromstring(book.read('xl/sharedStrings.xml')) if 'xl/sharedStrings.xml' in book.namelist() else None
  rows=[]
  for row in ET.fromstring(book.read('xl/worksheets/sheet1.xml')).findall('.//m:row',NS):
   vals={}
   for cell in row.findall('m:c',NS):
    col=re.sub(r'\d','',cell.attrib['r'])
    if col not in ['A','B','C']:continue
    value=cell.find('m:v',NS)
    if value is None:continue
    val=value.text
    if cell.attrib.get('t')=='s':val=''.join(strings[int(val)].itertext())
    vals[col]=val
   identifier=vals.get('A','').strip()
   if re.fullmatch(r'[VBHG]\d+(?:_\d+)?',identifier) and 'B' in vals and 'C' in vals:
    rows.append((identifier,float(vals['B']),float(vals['C'])))
 if len(rows)!=63:raise RuntimeError('Unexpected location table layout; no file written')
 with (ROOT/'config/sites.csv').open('w',newline='') as out:
  w=csv.writer(out);w.writerow(['site_id','latitude_deg','longitude_deg']);w.writerows(rows)
 print('Retained exactly 63 identifiers and coordinate pairs; no other columns retained.')
if __name__=='__main__':main()
