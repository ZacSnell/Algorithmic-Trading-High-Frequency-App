from pathlib import Path
import tempfile
import shutil


def atomic_save_bytes(target_path: Path, data: bytes):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=str(target_path.parent)) as tf:
        tf.write(data)
        temp_name = Path(tf.name)
    # move to final location atomically
    shutil.move(str(temp_name), str(target_path))


def atomic_save_object(target_path: Path, obj, joblib):
    # Save via joblib to a temp file then move
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = target_path.parent / (target_path.name + ".tmp")
    joblib.dump(obj, tmp)
    tmp.rename(target_path)
