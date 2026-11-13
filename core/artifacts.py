"""Artifacts are produced by this app only; never unpickle uploaded models."""
import json
from pathlib import Path
import uuid
import joblib
from core.database import ROOT, connect, now


def save_run(path, algorithm, result, pid=None):
    directory = ROOT / "models" / Path(path).stem
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{algorithm}-{pid or 'all'}-{uuid.uuid4().hex}.joblib"
    joblib.dump(result, target)
    with connect(path) as db:
        db.execute("INSERT INTO model_runs(algorithm,product_id,trained_at,data_cutoff,data_signature,metrics_json,artifact_path) VALUES(?,?,?,?,?,?,?)",
                   (algorithm, int(pid) if pid is not None else None, now(), result["cutoff"], result["signature"], json.dumps(result["metrics"], default=str), str(target.relative_to(ROOT))))
    return target


def latest_run(path, algorithm, pid=None):
    with connect(path) as db:
        row = db.execute("SELECT * FROM model_runs WHERE algorithm=? AND product_id IS ? ORDER BY id DESC LIMIT 1", (algorithm, int(pid) if pid is not None else None)).fetchone()
    if not row:
        return None, None
    metadata = dict(row)
    target = (ROOT/metadata["artifact_path"]).resolve()
    if not target.is_relative_to((ROOT/"models").resolve()) or not target.is_file():
        return None, None
    return joblib.load(target), metadata
