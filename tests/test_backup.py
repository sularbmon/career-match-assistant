import hashlib
import json
from zipfile import ZipFile
import pytest
from scripts.backup import bundle
from scripts.restore import verify_archive


def test_backup_includes_workspace_data_and_excludes_credentials(tmp_path):
    root=tmp_path/'workspace';(root/'uploads').mkdir(parents=True);(root/'.local').mkdir()
    (root/'uploads'/'cv.pdf').write_bytes(b'private cv')
    (root/'.local'/'career-profile.json').write_text('{"name":"Example"}')
    for filename in ('gmail-token.json','gmail-client.json'):(root/'.local'/filename).write_text('SECRET')
    (root/'.env').write_text('SECRET')
    dump=tmp_path/'database.dump';dump.write_bytes(b'database snapshot')
    destination=root/'.local'/'backups'/'test.zip'
    bundle(root,dump,destination)
    with ZipFile(destination) as archive:
        assert set(archive.namelist())=={'database.dump','uploads/cv.pdf','profile/career-profile.json','manifest.json'}
        manifest=json.loads(archive.read('manifest.json'))
        for item in manifest['files']:
            assert hashlib.sha256(archive.read(item['name'])).hexdigest()==item['sha256']
    with pytest.raises(FileExistsError):bundle(root,dump,destination)
    assert verify_archive(destination)['version']==1


def test_restore_verifier_rejects_path_traversal(tmp_path):
    path=tmp_path/'bad.zip'
    with ZipFile(path,'w') as archive:
        archive.writestr('../outside.txt','bad')
    with pytest.raises(ValueError,match='Unsafe backup path'):verify_archive(path)
