#!/usr/bin/env python3
"""Fast CTC TRA mask -> centroid CSV extractor v2.4.
Requires Pillow and NumPy. Uses CTC *_GT/TRA/man_track###.tif masks and man_track.txt.
"""
import argparse, zipfile, csv, re, io, hashlib
from pathlib import Path
from PIL import Image
import numpy as np

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def extract(zip_path, out_csv):
    zip_path=Path(zip_path); out_csv=Path(out_csv)
    source_id='ctc_fluo_n2dh_gowt1_real_zip_v24'
    dataset_name='Fluo-N2DH-GOWT1'; doi='10.5281/zenodo.15608211'; lic='CC-BY-4.0'
    zip_sha=sha256(zip_path)
    fields=['source_id','sample_id','clock_domain','time_s','sensor_id','sensor_kind','x','y','z','channel','value','uncertainty','track_id','frame','centroid_x','centroid_y','centroid_z','area','sequence_id','license','citation_key','dataset_name','doi','parent_track_id','start_frame','end_frame','source_zip_sha256']
    rows=[]
    with zipfile.ZipFile(zip_path) as z:
        seqs=sorted({m.group(1) for n in z.namelist() for m in [re.match(r'Fluo-N2DH-GOWT1/(\d\d)_GT/TRA/', n)] if m})
        for seq in seqs:
            base=f'Fluo-N2DH-GOWT1/{seq}_GT/TRA/'
            track_meta={}
            try:
                for line in z.read(base+'man_track.txt').decode().strip().splitlines():
                    parts=line.strip().split()
                    if len(parts)>=4:
                        tid,start,end,parent=parts[:4]
                        track_meta[tid]=(start,end,parent)
            except KeyError:
                pass
            names=[n for n in z.namelist() if n.startswith(base+'man_track') and n.endswith('.tif')]
            def frame_of(n):
                m=re.search(r'man_track(\d+)\.tif$',n); return int(m.group(1)) if m else -1
            for name in sorted(names,key=frame_of):
                frame=frame_of(name)
                arr=np.array(Image.open(io.BytesIO(z.read(name))))
                labels=np.unique(arr); labels=labels[labels>0]
                if labels.size==0: continue
                flat=arr.ravel(); maxlab=int(labels.max())
                counts=np.bincount(flat, minlength=maxlab+1)
                yy,xx=np.indices(arr.shape)
                sx=np.bincount(flat, weights=xx.ravel(), minlength=maxlab+1)
                sy=np.bincount(flat, weights=yy.ravel(), minlength=maxlab+1)
                for lab in labels:
                    lab=int(lab); area=int(counts[lab])
                    if area<=0: continue
                    cx=float(sx[lab]/area); cy=float(sy[lab]/area); cz=0.0
                    start,end,parent=track_meta.get(str(lab),('','',''))
                    rows.append({'source_id':source_id,'sample_id':f'{dataset_name}_{seq}_t{frame:03d}_track{lab}','clock_domain':'ctc_frame','time_s':f'{float(frame):.6f}','sensor_id':f'{dataset_name}_{seq}','sensor_kind':'ctc_tracking_centroid','x':f'{cx:.6f}','y':f'{cy:.6f}','z':f'{cz:.6f}','channel':'cell_centroid_motion','value':f'{area:.6f}','uncertainty':'0.000000','track_id':f'{seq}_{lab}','frame':str(frame),'centroid_x':f'{cx:.6f}','centroid_y':f'{cy:.6f}','centroid_z':f'{cz:.6f}','area':str(area),'sequence_id':seq,'license':lic,'citation_key':'ctc_fluo_n2dh_gowt1_zenodo_15608211','dataset_name':dataset_name,'doi':doi,'parent_track_id':parent,'start_frame':start,'end_frame':end,'source_zip_sha256':zip_sha})
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    return {'rows':len(rows),'tracks':len(set(r['track_id'] for r in rows)),'sha256':zip_sha,'out_csv':str(out_csv)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--zip', required=True)
    ap.add_argument('--out-csv', required=True)
    args=ap.parse_args()
    print(extract(args.zip,args.out_csv))
if __name__=='__main__': main()
