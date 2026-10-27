from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from scripts.backup import create_backup

router=APIRouter()


@router.post('/backup')
def backup():
    try:
        path=create_backup()
    except Exception as exc:
        raise HTTPException(500,'Backup failed. Check PostgreSQL tools and local disk access.') from exc
    return FileResponse(path,filename=path.name,media_type='application/zip')
