#!/usr/bin/env python3
"""Retrieve agency imagery independently. No author-hosted data are accessed.

Python performs network/file I/O and coordinate reprojection only. Spectral
calibration, cloud screening, medians, transforms and statistics belong to C++.
"""
import argparse
import concurrent.futures
import csv
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import threading
import time

import numpy as np
import requests
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.vrt import WarpedVRT

ROOT = Path(__file__).resolve().parents[1]
API = 'https://planetarycomputer.microsoft.com/api/stac/v1'
ASSETS = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'qa_pixel', 'qa_radsat']
lock = threading.Lock()
tokens = {}

def request(method, url, **kwargs):
    for attempt in range(5):
        try:
            response = requests.request(method, url, timeout=90, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == 4:
                raise RuntimeError('HTTP request failed: ' + url.split('?')[0]) from None
            time.sleep(min(2**attempt, 10))

def sign(url):
    from urllib.parse import urlparse
    u = urlparse(url)
    account = u.netloc.split('.')[0]
    container = u.path.split('/')[1]
    key = (account, container)
    with lock:
        if key not in tokens or time.time() - tokens[key][0] > 1800:
            d = request('GET', 'https://planetarycomputer.microsoft.com/api/sas/v1/token/' + account + '/' + container,
                        params={'_independent_request': str(time.time_ns())}).json()
            tokens[key] = (time.time(), d['token'])
    return url + '?' + tokens[key][1]

def catalog(region):
    pinned = ROOT / 'data/manifests' / (region['id'] + '.json')
    if pinned.exists():
        return json.loads(pinned.read_text())['features']
    path = ROOT / 'data/stac' / (region['id'] + '.json')
    if path.exists():
        return json.loads(path.read_text())['features']
    body = {'collections': ['landsat-c2-l2'], 'bbox': region['bbox'],
            'datetime': f"{min(region['years'])}-01-01T00:00:00Z/{max(region['years'])}-12-31T23:59:59Z", 'limit': 1000}
    features = []
    url, method = API + '/search', 'POST'
    while url:
        d = request(method, url, **({'json': body} if method == 'POST' else {})).json()
        features.extend(d.get('features', []))
        nxt = next((x for x in d.get('links', []) if x['rel'] == 'next'), None)
        if nxt:
            url, method = nxt['href'], nxt.get('method', 'GET')
            if method == 'POST':
                body = dict(body, **nxt.get('body', {})) if nxt.get('merge') else nxt.get('body', body)
        else:
            url = None
    unique = {x['id']: x for x in features}
    features = sorted(unique.values(), key=lambda x: x['id'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'features': features}, indent=2))
    return features

def get_grid(region):
    xmin, ymin, xmax, ymax = transform_bounds('EPSG:4326', region['epsg'], *region['bbox'], densify_pts=21)
    dx = region['resolution_m']
    xmin, ymin, xmax, ymax = [v*dx for v in (math.floor(xmin/dx), math.floor(ymin/dx), math.ceil(xmax/dx), math.ceil(ymax/dx))]
    width, height = round((xmax-xmin)/dx), round((ymax-ymin)/dx)
    return width, height, from_origin(xmin, ymax, dx, dx)

def download_scene(item, region, directory, width, height, transform):
    target = directory / (item['id'] + '.u16')
    sensor = int(item['properties']['platform'].split('-')[-1])
    record = {'date': item['properties']['datetime'][:10], 'sensor': sensor, 'file': target.name,
              'scene_id': item['id'], 'source': 'USGS Landsat Collection 2 Level 2 via Microsoft Planetary Computer'}
    if target.exists() and target.stat().st_size == 8*width*height*2:
        record['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        return record
    arrays = []
    # Range-read provider COGs; nearest-neighbour preserves DN and QA integers.
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', GDAL_HTTP_MAX_RETRY='3',
                      GDAL_HTTP_RETRY_DELAY='2', GDAL_HTTP_TIMEOUT='90',
                      GDAL_CACHEMAX=128*1024*1024, CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.TIF,.tif'):
        for asset in ASSETS:
            url = sign(item['assets'][asset]['href'])
            try:
                with rasterio.open(url) as src:
                    with WarpedVRT(src, crs=region['epsg'], transform=transform,
                                   width=width, height=height, resampling=Resampling.nearest,
                                   nodata=0) as vrt:
                        arrays.append(vrt.read(1, out_dtype='uint16'))
            except Exception:
                raise RuntimeError('COG read failed for ' + item['id'] + '/' + asset) from None
    array = np.stack(arrays).astype('<u2')
    temporary = target.with_suffix('.part')
    array.tofile(temporary)
    temporary.replace(target)
    record['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    return record

def acquire(region, workers, max_per_year=None):
    directory = ROOT / 'data/raw' / region['id']
    directory.mkdir(parents=True, exist_ok=True)
    width, height, transform = get_grid(region)
    (directory / 'grid.txt').write_text(f'{width} {height} {transform.a} {transform.e} {transform.c} {transform.f} {region["epsg"]}\n')
    items = [x for x in catalog(region) if int(x['properties']['datetime'][:4]) in region['years']
             and x['properties']['platform'] in ['landsat-5', 'landsat-7', 'landsat-8']
             and all(k in x['assets'] for k in ASSETS)]
    pinned = ROOT / 'data/manifests' / (region['id'] + '.json')
    pinned.parent.mkdir(parents=True, exist_ok=True)
    minimal = [{'id': x['id'], 'properties': {k:x['properties'][k] for k in
                ['datetime','platform','eo:cloud_cover'] if k in x['properties']},
                'assets': {k:{'href':x['assets'][k]['href'].split('?')[0]} for k in ASSETS}}
               for x in items]
    pinned.write_text(json.dumps({'features':minimal}, indent=2))
    # Optional reconnaissance is explicitly distinct from complete annual input.
    if max_per_year:
        selected = []
        for year in region['years']:
            yr = [x for x in items if int(x['properties']['datetime'][:4]) == year]
            selected.extend(sorted(yr, key=lambda x: (x['properties'].get('eo:cloud_cover', 100), x['id']))[:max_per_year])
        items = selected
    print(f"{region['id']}: {width} x {height}, {len(items)} scenes", flush=True)
    successes, errors = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        tasks = {pool.submit(download_scene, x, region, directory, width, height, transform): x for x in items}
        for n, task in enumerate(concurrent.futures.as_completed(tasks), 1):
            try:
                successes.append(task.result())
            except Exception as e:
                errors.append({'scene_id': tasks[task]['id'], 'reason': str(e).split('?')[0]})
            if n % 10 == 0 or n == len(tasks):
                print(f"{region['id']}: {n}/{len(tasks)} attempted; {len(errors)} failures", flush=True)
            # Checkpoint successful downloads, so interruption loses no provenance.
            with (directory/'scenes.csv').open('w') as f:
                writer=csv.writer(f); writer.writerow(['date','sensor','file'])
                for row in sorted(successes,key=lambda x:(x['date'],x['scene_id'])):
                    writer.writerow([row['date'],row['sensor'],row['file']])
    provenance = ROOT/'data/provenance'
    provenance.mkdir(parents=True, exist_ok=True)
    (provenance/(region['id']+'.json')).write_text(json.dumps({
        'region':region, 'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'max_scenes_per_year':max_per_year, 'catalog_scenes_selected':len(items),
        'successful_scenes':successes, 'failed_scenes':errors,
        'resampling':'nearest', 'raw_array_order':ASSETS},indent=2))
    if not successes:
        raise RuntimeError('No raw scenes acquired for '+region['id'])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='config/regions.json')
    parser.add_argument('--region',default='all')
    parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--max-per-year',type=int)
    args=parser.parse_args()
    regions=json.loads((ROOT/args.config).read_text())
    for region in regions:
        if args.region in ['all',region['id']]:
            acquire(region,args.workers,args.max_per_year)
if __name__=='__main__':
    main()
