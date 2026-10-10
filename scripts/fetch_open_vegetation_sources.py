"""Fetch the CC0 source assets for the open-vegetation (island-tree + palm) layer.

Downloads (no runtime network use; provenance is recorded locally):
  - Poly Haven island_tree_03 (CC0, Rico Cilliers / Rob Tuytel): 1k glTF + its
    include files + the leaves alpha PNG, plus the files API response as the
    md5 catalogue consumed by build_open_vegetation.py --prepare.
  - OpenGameArt palm tree v2 (CC0, Yughues / Nobiax): palm_tree_v2.7z, unpacked
    into the palm-source/ directory that build_open_vegetation.py reads.

Run: $env:PYTHONUTF8='1'; .venv/Scripts/python.exe scripts/fetch_open_vegetation_sources.py
"""
from pathlib import Path
import urllib.request, json, hashlib, io, sys, time
import py7zr

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'artifacts/driving-experience-candidate/sources'
OUT = ROOT / 'artifacts/driving-experience-candidate/vegetation'
SOURCE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
PALM_SRC = OUT / 'palm-source'
PALM_SRC.mkdir(parents=True, exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0 (Shenchengji local asset preparation; CC0 sources)'}


def request(url, timeout=300):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def fetch(url, path, md5=None, retries=3):
    for attempt in range(1, retries + 1):
        try:
            data = request(url).read()
            if md5 and hashlib.md5(data).hexdigest() != md5:
                raise ValueError(f'md5 mismatch for {url}')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            print(f'  ok {path.name} ({len(data)} bytes)', flush=True)
            return data
        except Exception as exc:
            print(f'  retry {attempt}/{retries} {url}: {type(exc).__name__} {exc}', flush=True)
            if attempt == retries:
                raise
            time.sleep(3)


def main():
    # 1. Poly Haven island_tree_03 metadata (this exact JSON is the catalogue
    #    build_open_vegetation.py --prepare asserts against).
    api = json.loads(request('https://api.polyhaven.com/files/island_tree_03').read())
    (SOURCE / 'island-tree-files.json').write_text(json.dumps(api, indent=2) + '\n')

    entry = api['gltf']['1k']['gltf']
    gltf_bytes = fetch(entry['url'], SOURCE / 'island-tree' / 'island_tree_03.gltf', entry['md5'])
    for relative, meta in entry['include'].items():
        target = SOURCE / 'island-tree' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        fetch(meta['url'], target, meta['md5'])
    # The leaves alpha is consumed from the vegetation output dir, not the source dir.
    alpha_meta = api['leaves_alpha']['1k']['png']
    fetch(alpha_meta['url'], OUT / 'island-leaves-alpha-source.png', alpha_meta['md5'])

    # 2. OpenGameArt palm tree v2 (7z archive; CC0, Yughues / Nobiax).
    palm_archive = SOURCE / 'palm-tree-v2.7z'
    fetch('https://opengameart.org/sites/default/files/palm_tree_v2.7z', palm_archive)
    with py7zr.SevenZipFile(str(palm_archive), 'r') as archive:
        names = archive.getnames()
        print('palm archive entries:', names, flush=True)
        archive.extractall(str(PALM_SRC))
    for found in PALM_SRC.rglob('*'):
        print('  extracted', found.relative_to(PALM_SRC), flush=True)

    print('\nSources staged under artifacts/driving-experience-candidate/', flush=True)
    print('Next: PYTHONUTF8=1 python scripts/build_open_vegetation.py --prepare', flush=True)


if __name__ == '__main__':
    main()
