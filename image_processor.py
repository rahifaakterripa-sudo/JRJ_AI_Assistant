import io
from typing import Tuple
from PIL import Image

class ImageProcessingError(Exception):
    pass

class ImageProcessor:
    MAX_FILE_SIZE_BYTES = 12 * 1024 * 1024  # 12 MB
    MIN_DIMENSION = 120                     # 120 px
    MAX_OPTIMAL_WIDTH = 1920                # Downscale if larger to speed up Gemini SLA
    MAX_OPTIMAL_HEIGHT = 1080

    @classmethod
    def validate_and_preprocess(cls, image_bytes: bytes) -> Tuple[bytes, Tuple[int, int]]:
        """
        Validates raw image bytes and prepares them for Gemini Vision.
        Returns: (processed_jpeg_bytes, (width, height))
        """
        if not image_bytes or len(image_bytes) == 0:
            raise ImageProcessingError("Empty image payload received.")

        if len(image_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise ImageProcessingError(
                f"Image size {len(image_bytes)/(1024*1024):.1f}MB exceeds limit of {cls.MAX_FILE_SIZE_BYTES/(1024*1024):.0f}MB."
            )

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
        except Exception as e:
            raise ImageProcessingError(f"Corrupted or invalid image file: {str(e)}")

        # Re-open after verify() (Pillow requirement)
        image = Image.open(io.BytesIO(image_bytes))

        # Check dimensions
        orig_width, orig_height = image.size
        if orig_width < cls.MIN_DIMENSION or orig_height < cls.MIN_DIMENSION:
            raise ImageProcessingError(
                f"Image resolution {orig_width}x{orig_height} is too small for accurate chart candle analysis. Minimum required is {cls.MIN_DIMENSION}x{cls.MIN_DIMENSION}."
            )

        # Convert to RGB if RGBA/P/Grayscale
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Downscale proportionally if larger than maximum optimal size for speed
        if orig_width > cls.MAX_OPTIMAL_WIDTH or orig_height > cls.MAX_OPTIMAL_HEIGHT:
            image.thumbnail((cls.MAX_OPTIMAL_WIDTH, cls.MAX_OPTIMAL_HEIGHT), Image.Resampling.LANCZOS)

        out_buffer = io.BytesIO()
        image.save(out_buffer, format="JPEG", quality=88, optimize=True)
        final_bytes = out_buffer.getvalue()

        return final_bytes, image.size
