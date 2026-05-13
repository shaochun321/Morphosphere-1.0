#!/usr/bin/env python3
import argparse, csv, os, re, tempfile, zipfile
from pathlib import Path

def find_masks(root):
    pats=[]
    for pat in ['**/*_GT/TRA/man_track*.tif','**/*_GT/TRA/man_track*.tiff','**/*_GT/SEG/man_seg*.tif','**/*_ST/SEG/*.tif']:
        pats.extend(Path(root).glob(pat))
    return sorted(set(pats))

def frame_from_name(name):
    m=re.search(r'(\d+)(?=\.tif)', name)
    return int(m.group(1)) if m else 0

def parse_track_txt(root):
    d={}
    for p in Path(root).glob('**/*_GT/TRA/man_track.txt'):
        for line in p.read_text(errors='ignore').splitlines():
            parts=line.split()
            if len(parts)>=4:
                d[parts[0]]={'start':parts[1],'end':parts[2],'parent':parts[3]}
    return d

def read_tif_centroids(path):
    try:
        from PIL import Image
    except Exception as e:
        raise SystemExit('Pillow is required for TIFF mask extraction. Install pillow or provide a centroid CSV. Original error: '+str(e))
    img=Image.open(path)
    w,h=img.size
    data=list(img.getdata())
    acc={}
    for idx,val in enumerate(data):
        try: lab=int(val)
        except Exception: continue
        if lab<=0: continue
        x=idx%w; y=idx//w
        if lab not in acc: acc[lab]=[0,0,0]
        acc[lab][0]+=x; acc[lab][1]+=y; acc[lab][2]+=1
    out=[]
    for lab,(sx,sy,n) in acc.items():
        out.append((str(lab), sx/n, sy/n, n))
    return out

def main():
    ap=argparse.ArgumentParser(description='Extract centroid CSV from CTC TRA/SEG masks.')
    ap.add_argument('--ctc-root')
    ap.add_argument('--zip')
    ap.add_argument('--out-csv', required=True)
    ap.add_argument('--dt-s', type=float, default=1.0)
    ap.add_argument('--source-id', default='ctc_real_external')
    ap.add_argument('--dataset-name', default='Fluo-N2DH-GOWT1')
    ap.add_argument('--doi', default='10.5281/zenodo.15608211')
    args=ap.parse_args()
    tmp=None
    if args.zip:
        tmp=tempfile.TemporaryDirectory(); root=tmp.name
        with zipfile.ZipFile(args.zip) as z: z.extractall(root)
    elif args.ctc_root:
        root=args.ctc_root
    else:
        raise SystemExit('provide --ctc-root or --zip')
    tracks=parse_track_txt(root)
    masks=find_masks(root)
    if not masks: raise SystemExit('no CTC TRA/SEG mask tiffs found')
    cols=['source_id','sample_id','clock_domain','time_s','sensor_id','sensor_kind','x','y','z','channel','value','uncertainty','track_id','frame','centroid_x','centroid_y','centroid_z','area','sequence_id','parent_track_id','start_frame','end_frame','license','citation_key','dataset_name','doi']
    with open(args.out_csv,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for p in masks:
            frame=frame_from_name(p.name); seq='unknown'
            for part in p.parts:
                if part in ['01','02']: seq=part
            for lab,x,y,area in read_tif_centroids(p):
                t=tracks.get(lab,{})
                w.writerow({'source_id':args.source_id,'sample_id':f'{seq}_{lab}_{frame:04d}','clock_domain':f'ctc_sequence_{seq}','time_s':f'{frame*args.dt_s:.6f}','sensor_id':f'track_{lab}','sensor_kind':'ctc_centroid','x':f'{x:.6f}','y':f'{y:.6f}','z':'0.0','channel':'cell_centroid_position','value':'1.0','uncertainty':'0.0','track_id':lab,'frame':frame,'centroid_x':f'{x:.6f}','centroid_y':f'{y:.6f}','centroid_z':'0.0','area':area,'sequence_id':seq,'parent_track_id':t.get('parent','0'),'start_frame':t.get('start',''),'end_frame':t.get('end',''),'license':'CC-BY-4.0','citation_key':'Cell Tracking Challenge / Zenodo 10.5281/zenodo.15608211','dataset_name':args.dataset_name,'doi':args.doi})
    print('wrote', args.out_csv, 'from', len(masks), 'mask files')
if __name__=='__main__': main()
