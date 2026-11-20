"""Capture or restore the prepared live-demo state.

Run once before the first rehearsal to capture data/demo.db and models/demo.
Run the same command before every later rehearsal to restore that snapshot.
Only the Demonstration workspace is touched; data/store.db is never modified.

    .venv/Scripts/python.exe rehearsal_reset.py

Use --refresh after deliberately changing the prepared demo state and wanting
that new state to become the baseline.

Stop the Streamlit server before capturing or restoring. The app may keep old
results in a browser session even after the files are restored.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEMO_DB = ROOT / "data" / "demo.db"
DEMO_MODELS = ROOT / "models" / "demo"
DEFAULT_BACKUP = ROOT / "tmp" / "demo-backup"


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _shown(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _database_files(path: Path) -> list[Path]:
    """The database plus any SQLite sidecars that may exist."""
    candidates = [path, Path(f"{path}-wal"), Path(f"{path}-shm")]
    return [item for item in candidates if item.is_file()]


def _read_metadata(backup: Path) -> dict:
    try:
        return json.loads((backup / "snapshot.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _describe(backup: Path) -> str:
    metadata = _read_metadata(backup)
    captured = metadata.get("captured_at", "unknown time")
    try:
        captured = datetime.fromisoformat(captured).strftime("%d %b %Y at %H:%M")
    except (TypeError, ValueError):
        pass
    files = metadata.get("models_files", "?")
    return f"snapshot captured {captured} - {files} model file(s)"


def capture(backup: Path) -> dict:
    if not DEMO_DB.is_file():
        raise FileNotFoundError(
            f"{DEMO_DB.relative_to(ROOT)} does not exist. Open the Demonstration workspace first."
        )
    if not DEMO_MODELS.is_dir():
        raise FileNotFoundError(
            f"{DEMO_MODELS.relative_to(ROOT)} does not exist. Run manage.py train-demo first."
        )

    staging = backup.with_name(backup.name + ".tmp")
    _remove(staging)
    staging.mkdir(parents=True)

    try:
        for item in _database_files(DEMO_DB):
            shutil.copy2(item, staging / item.name)
        shutil.copytree(DEMO_MODELS, staging / "models-demo")

        metadata = {
            "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "models_files": sum(1 for item in (staging / "models-demo").rglob("*") if item.is_file()),
            "source": "Demonstration workspace",
        }
        (staging / "snapshot.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )

        _remove(backup)
        staging.rename(backup)
        return metadata
    except Exception:
        _remove(staging)
        raise


def restore(backup: Path) -> dict:
    backup_db = backup / "demo.db"
    backup_models = backup / "models-demo"
    if not backup_db.is_file() or not backup_models.is_dir():
        raise FileNotFoundError(
            f"No complete snapshot in {_shown(backup)}. "
            "Run with --refresh to capture the current prepared state."
        )

    # Replace the database atomically, then remove any stale sidecars.
    data_dir = DEMO_DB.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    staged_db = data_dir / ".demo.db.restore"
    shutil.copy2(backup_db, staged_db)
    for sidecar in (Path(f"{DEMO_DB}-wal"), Path(f"{DEMO_DB}-shm")):
        sidecar.unlink(missing_ok=True)
    os.replace(staged_db, DEMO_DB)
    for suffix in ("-wal", "-shm"):
        source = backup / f"demo.db{suffix}"
        if source.is_file():
            shutil.copy2(source, Path(f"{DEMO_DB}{suffix}"))

    # Replace the model directory only after the database copy succeeds.
    demo_models_parent = DEMO_MODELS.parent
    demo_models_parent.mkdir(parents=True, exist_ok=True)
    staged_models = demo_models_parent / ".demo.restore"
    _remove(staged_models)
    shutil.copytree(backup_models, staged_models)
    _remove(DEMO_MODELS)
    staged_models.rename(DEMO_MODELS)

    return _read_metadata(backup)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture or restore the prepared Demonstration workspace for rehearsal."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="replace the saved snapshot with the current demo state instead of restoring it",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    backup = args.backup_dir if args.backup_dir.is_absolute() else ROOT / args.backup_dir
    print("Stop the Streamlit server before using this script, then start it again afterward.")

    try:
        if args.refresh:
            capture(backup)
            print(f"Saved a new baseline in {_shown(backup)}.")
            print(f"  {_describe(backup)}")
            print("Run this command again after rehearsing to restore it.")
            return 0

        if not (backup / "demo.db").is_file():
            capture(backup)
            print(f"Baseline captured in {_shown(backup)}.")
            print(f"  {_describe(backup)}")
            print("The current app state is unchanged. Rehearse, then run this command again to restore it.")
            return 0

        restore(backup)
        print(f"Restored the Demonstration workspace from {_shown(backup)}.")
        print(f"  {_describe(backup)}")
        print("Your store records were not touched. Start the app with launch.bat.")
        return 0
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
