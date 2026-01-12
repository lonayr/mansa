import os
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename: str, allowed_exts: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_exts

def save_file(file_storage, folder: str, allowed_exts: set) -> str:
    if not file_storage or file_storage.filename == "":
        return ""
    filename = secure_filename(file_storage.filename)
    if not allowed_file(filename, allowed_exts):
        raise ValueError("امتداد الملف غير مسموح.")
    path = os.path.join(folder, filename)
    file_storage.save(path)
    return path
