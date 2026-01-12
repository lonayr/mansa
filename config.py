import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "سر-قوي-لتأمين-النماذج"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    PROFILE_UPLOAD_FOLDER = os.path.join(BASE_DIR, "profile_images")
    SETTINGS_FOLDER = os.path.join(BASE_DIR, "settings")

    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB

    COURSE_ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "webm", "pdf"}
    IMAGE_ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
