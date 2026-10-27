"""Start the personal local workspace with additive database updates."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    if not (ROOT/'.env').exists():
        raise SystemExit('Create .env from .env.example and set DATABASE_URL first.')
    subprocess.run([sys.executable,'-m','app.database.init_db'],cwd=ROOT,check=True)
    print(f'Open http://127.0.0.1:{args.port}/dashboard#today',flush=True)
    subprocess.run([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1',
                    '--port',str(args.port),'--reload'],cwd=ROOT,check=True)
