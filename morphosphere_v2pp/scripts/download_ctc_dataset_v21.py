#!/usr/bin/env python3
import argparse, hashlib, json, urllib.request
from pathlib import Path

def md5(path):
    h=hashlib.md5()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description='Download a selected CTC dataset zip and verify md5.')
    ap.add_argument('--manifest', default='morphosphere_v2pp/data/ctc_download_manifest_v21.json')
    ap.add_argument('--out-dir', default='external_data/ctc')
    args=ap.parse_args()
    m=json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    out_dir=Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out=out_dir/m['file_name']
    urllib.request.urlretrieve(m['download_url'], out)
    got=md5(out)
    ok=(got.lower()==m['expected_md5'].lower())
    print(json.dumps({'path':str(out),'md5':got,'expected_md5':m['expected_md5'],'ok':ok}, indent=2))
    if not ok: raise SystemExit('md5 mismatch')
if __name__=='__main__': main()
