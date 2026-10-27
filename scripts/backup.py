"""Private local backup of PostgreSQL, uploaded documents, and personal profile."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]


def pg_tool(name):
    found=shutil.which(name)
    if found:return found
    psql=shutil.which('psql')
    if psql:
        sibling=Path(psql).with_name(name+('.exe' if os.name=='nt' else ''))
        if sibling.is_file():return str(sibling)
    raise RuntimeError(f'{name} is required. Add PostgreSQL bin to PATH.')


def bundle(root,dump_path,destination):
    root=Path(root).resolve();destination=Path(destination)
    if destination.exists():raise FileExistsError('A backup already exists at that path')
    manifest={'version':1,'created_at':datetime.now(timezone.utc).isoformat(),
              'excluded':['OAuth credentials and tokens','.env','Git repository'], 'files':[]}
    sources=[('database.dump',Path(dump_path))]
    uploads=root/'uploads'
    if uploads.exists() and uploads.resolve().is_relative_to(root):
        for path in uploads.rglob('*'):
            if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(uploads.resolve()):
                sources.append((path.relative_to(root).as_posix(),path))
    profile=root/'.local'/'career-profile.json'
    if profile.is_file() and not profile.is_symlink() and profile.resolve().is_relative_to(root):sources.append(('profile/career-profile.json',profile))
    destination.parent.mkdir(parents=True,exist_ok=True)
    try:
        with ZipFile(destination,'x',ZIP_DEFLATED) as archive:
            for name,path in sources:
                digest=hashlib.sha256()
                with path.open('rb') as source,archive.open(name,'w',force_zip64=True) as output:
                    for chunk in iter(lambda:source.read(1024*1024),b''):
                        digest.update(chunk);output.write(chunk)
                manifest['files'].append({'name':name,'sha256':digest.hexdigest()})
            archive.writestr('manifest.json',json.dumps(manifest,indent=2))
        with ZipFile(destination) as archive:
            if archive.testzip() is not None:raise RuntimeError('Backup integrity check failed')
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination


def create_backup(output=None):
    import sys
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from app.database.session import engine
    url=engine.url
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=Path(output) if output else ROOT/'.local'/'backups'/f'career-workspace-{stamp}.zip'
    environment=os.environ.copy()
    if url.password:environment['PGPASSWORD']=url.password
    with tempfile.TemporaryDirectory(prefix='career-backup-') as directory:
        dump=Path(directory)/'database.dump'
        command=[pg_tool('pg_dump'),'--no-password','--format=custom','--no-owner','--no-privileges',
                 '--host',url.host or 'localhost','--port',str(url.port or 5432),
                 '--username',url.username or 'postgres','--file',str(dump),url.database]
        try:
            subprocess.run(command,env=environment,check=True,timeout=120,capture_output=True)
            subprocess.run([pg_tool('pg_restore'),'--list',str(dump)],check=True,timeout=30,capture_output=True)
        except subprocess.SubprocessError as exc:
            raise RuntimeError('PostgreSQL backup failed. Check database access and PostgreSQL client version.') from exc
        return bundle(ROOT,dump,output)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    print(create_backup(args.output))
