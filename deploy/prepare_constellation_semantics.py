"""Prepare local public evidence semantics; no provider inference or trading I/O.

Run inside the personal image, with its existing runtime volume and local mode.
--download fetches only two hash-pinned public model files through the hf CLI.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from cloud_app.config import get_settings
from cloud_app.constellation_embeddings import FILES, MODEL_REPO, MODEL_REVISION, model_directory, verify
from cloud_app.constellation_index import prepare


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--copy-model-from',type=Path)
    parser.add_argument('--batch-size',type=int,choices=(1,2,4,8),default=8)
    args=parser.parse_args()
    settings=get_settings();target=model_directory(settings)
    if any(p.is_symlink() for p in (target,*target.parents)):raise SystemExit('Unsafe model directory')
    target.mkdir(parents=True,exist_ok=True,mode=0o700)
    if args.copy_model_from:
        verify(args.copy_model_from)
        for filename in FILES:
            path=target/filename;path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            if not path.exists():
                shutil.copyfile(args.copy_model_from/filename,path);path.chmod(0o600)
    if args.download:
        subprocess.run(['hf','download',MODEL_REPO,*FILES,'--revision',MODEL_REVISION,'--local-dir',str(target),'--max-workers','1'],
                       check=True,env={**os.environ,'HF_HUB_DISABLE_IMPLICIT_TOKEN':'1','HF_HUB_DISABLE_XET':'1'})
    verify(target)
    print(json.dumps(prepare(settings,batch_size=args.batch_size),ensure_ascii=False))


if __name__=='__main__':main()
