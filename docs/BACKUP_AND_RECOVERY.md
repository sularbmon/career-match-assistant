# Private workspace backup and recovery

## Create a backup

Use Accounts → Create and download backup. The app retains a copy under `.local/backups` and downloads a ZIP containing:

- A PostgreSQL custom-format database snapshot, including roles, comparisons, contacts, history, and preferences.
- Uploaded resumes and documents under `uploads/`.
- The local personal profile, if configured.
- A manifest with SHA-256 checksums.

OAuth client credentials, Gmail tokens, `.env`, and Git history are excluded. The archive is not encrypted and contains personal information. Store it privately. It is a data backup, not a replacement for a copy of the application source and dependency setup.

Or create a backup from PowerShell:

```powershell
.\.venv\Scripts\python.exe scripts/backup.py
```

PostgreSQL's `pg_dump` and `pg_restore` must be available through PATH or beside `psql`. The launcher does not schedule backups; create one after important updates. Avoid editing workspace data during a backup so its database snapshot and uploaded files represent the same point in your work.

## Verify an archive

```powershell
.\.venv\Scripts\python.exe scripts/restore.py "C:\path\to\career-workspace-backup.zip"
```

This checks archive paths, manifest entries, and file checksums without writing to a database. It does not prove the database is restorable; a separate restore test does that.

## Restore separately before switching over

Create a separate empty PostgreSQL database on the same configured server:

```powershell
psql -h localhost -U postgres -W -c "CREATE DATABASE career_recovered;"
.\.venv\Scripts\python.exe scripts/restore.py "C:\path\to\career-workspace-backup.zip" --database career_recovered --files-dir "C:\path\to\empty-recovered-files"
```

The script refuses the active workspace database, an existing public table set, or a nonempty output directory. PostgreSQL restore runs in one transaction. Files are restored separately under the chosen directory as `uploads/` and `.local/career-profile.json`; account tokens must be authorized again. If file recovery fails after the database transaction completes, keep the archive, inspect disk access, and recover into another fresh database and empty directory.

Review the recovered files and database before changing anything in your active workspace. To switch, stop the API, preserve the current workspace, set DATABASE_URL to the recovered database, and place the recovered `uploads/` and personal profile in a separate copy of this application. Then start that copy. Do not overwrite your active uploaded files casually.

## Verification performed

A real local backup was checked with pg_restore and restored into an isolated temporary database. The initial check recovered 10 application tables, checked the stored resume count, and recovered the personal profile file. A later check after adding job discovery recovered all 11 current tables and compared their names with the active schema. Each temporary database was removed; the active database was not replaced. Automated tests cover secret exclusion, file checksums, overwrite refusal, and unsafe archive paths. These checks do not replace periodically testing recovery with your own latest backup.
