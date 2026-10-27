"""Verify a backup, or restore into a separate empty database and file directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import re
import sys
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.backup import pg_tool


def verify_archive(path):
    with ZipFile(path) as archive:
        names=archive.namelist()
        if len(set(names))!=len(names):raise ValueError('Duplicate archive entries')
        for name in names:
            parts=PurePosixPath(name)
            if '\\' in name or ':' in name or parts.is_absolute() or '..' in parts.parts:
                raise ValueError('Unsafe backup path')
            if name not in ('manifest.json','database.dump','profile/career-profile.json') and not name.startswith('uploads/'):
                raise ValueError('Unexpected backup entry')
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('version')!=1:raise ValueError('Unsupported backup version')
        entries=manifest['files']
        if {entry['name'] for entry in entries} != set(names)-{'manifest.json'}:
            raise ValueError('Backup manifest does not match archive')
        if 'database.dump' not in names:raise ValueError('Database snapshot is missing')
        for entry in entries:
            digest=hashlib.sha256()
            with archive.open(entry['name']) as source:
                for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
            if digest.hexdigest()!=entry['sha256']:raise ValueError('Backup checksum mismatch')
    return manifest


def restore(path,database,files_dir):
    verify_archive(path)
    from app.database.session import engine
    from sqlalchemy import create_engine,text
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',database):raise ValueError('Use a simple PostgreSQL database name')
    if database==engine.url.database:raise ValueError('Restore requires a separate database, not your active workspace')
    target=Path(files_dir).resolve()
    if target.exists() and any(target.iterdir()):raise ValueError('Restore files directory must be empty')
    destination=engine.url.set(database=database)
    check=create_engine(destination)
    try:
        with check.connect() as connection:
            count=connection.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")).scalar()
            if count:raise ValueError('Restore database must have no public tables')
    finally:check.dispose()
    environment=os.environ.copy()
    if destination.password:environment['PGPASSWORD']=destination.password
    with tempfile.TemporaryDirectory(prefix='career-restore-') as temporary,ZipFile(path) as archive:
        dump=Path(temporary)/'database.dump'
        with archive.open('database.dump') as source,dump.open('wb') as output:shutil.copyfileobj(source,output)
        command=[pg_tool('pg_restore'),'--no-password','--single-transaction','--exit-on-error','--no-owner','--no-privileges',
                 '--host',destination.host or 'localhost','--port',str(destination.port or 5432),
                 '--username',destination.username or 'postgres','--dbname',database,str(dump)]
        subprocess.run(command,env=environment,check=True,timeout=120,capture_output=True)
        for name in archive.namelist():
            if name.startswith('uploads/') or name=='profile/career-profile.json':
                relative='.local/career-profile.json' if name.startswith('profile/') else name
                output=(target/relative).resolve()
                if not output.is_relative_to(target):raise ValueError('Unsafe output path')
                output.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(name) as source,output.open('wb') as sink:shutil.copyfileobj(source,sink)
    return target


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('--database');parser.add_argument('--files-dir');args=parser.parse_args()
    if args.database:
        if not args.files_dir:parser.error('--files-dir is required with --database')
        print('Restored files:',restore(args.archive,args.database,args.files_dir))
    else:
        manifest=verify_archive(args.archive);print('Backup verified:',len(manifest['files']),'entries; created',manifest['created_at'])
