from PIL import Image
import io
import logging
from PIL import UnidentifiedImageError

logger = logging.getLogger(__name__)

def compress_image(image_path, quality=40, size=(1200, 1200), output_format=None):
    output = io.BytesIO()
    try:
        with Image.open(image_path) as img:
            if not output_format:
                output_format = img.format
            img.thumbnail(size)
            img.save(output, format=output_format, quality=quality)
            output.seek(0)
        return output
    except FileNotFoundError:
        logger.warning(f"File {image_path} not found.")
    except UnidentifiedImageError:
        logger.warning(f"Cannot identify image file {image_path}.")
    except Exception as e:
        logger.warning(f"Error compressing image: {e}")
    return None

