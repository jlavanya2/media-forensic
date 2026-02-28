import os

ALLOWED_EXTENSIONS = {
    "image": ["jpg", "jpeg", "png"],
    "audio": ["mp3", "wav"],
    "video": ["mp4", "mov"]
}

def validate_file(filename):
    ext = filename.split('.')[-1].lower()

    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category

    return None