#!/usr/bin/env python3
"""Inspect newly granted ASL3DWord files WITHOUT assuming dataset shape or executing pickle.

Usage: python tools/inspect_asl3dword.py path/to/ASL3DWord [--max-files 30]
Only .npy/.npz are loaded, with allow_pickle=False. Untrusted .pkl/.pt are listed
and intentionally not deserialized. Metadata is printed; nothing is modified.
"""
import argparse
from pathlib import Path
import numpy as np


def summarize(path: Path):
    try:
        if path.suffix.lower() == '.npy':
            a = np.load(path, mmap_mode='r', allow_pickle=False)
            return f'array shape={a.shape}, dtype={a.dtype}, finite={bool(np.isfinite(a).all()) if np.issubdtype(a.dtype, np.number) and a.size<2_000_000 else "not checked"}'
        if path.suffix.lower() == '.npz':
            with np.load(path, allow_pickle=False) as z:
                return 'keys: '+', '.join(f'{key}: {z[key].shape} {z[key].dtype}' for key in z.files)
        if path.suffix.lower() in ('.pkl', '.pickle', '.pt', '.pth'):
            return 'BINARY SERIALIZATION: not opened (may execute code when deserialized); use official trusted tools'
        return 'listed only'
    except Exception as exc:
        return f'could not safely inspect: {exc}'


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('path', type=Path, help='Extracted dataset path, or one file')
    ap.add_argument('--max-files', type=int, default=30)
    args=ap.parse_args()
    if not args.path.exists():ap.error(f'Not found: {args.path}')
    files = [args.path] if args.path.is_file() else sorted(p for p in args.path.rglob('*') if p.is_file())
    print(f'Discovered {len(files)} files. Displaying first {args.max_files}.')
    for f in files[:args.max_files]:
        print(f'\n{f} ({f.stat().st_size:,} bytes)')
        print('  '+summarize(f))
    print('\nIMPORTANT: Metadata inspection is not retargeting. ASL3DWord pose data must be interpreted with the authors\' mapping and licensed SMPL-X model before exporting 3D joint positions.')

if __name__=='__main__':main()
