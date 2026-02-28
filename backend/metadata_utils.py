from PIL import Image
from PIL.ExifTags import TAGS

def extract_image_metadata(path):
    metadata = {}
    try:
        img = Image.open(path)
        exif = img._getexif()
        if exif:
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                metadata[decoded] = str(value)
    except:
        pass
    return metadata