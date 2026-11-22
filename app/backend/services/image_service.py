import os
from typing import Tuple
from PIL import Image, ImageOps
from app.backend.services.provider_service import provider_service
from app.backend.core.guardrails import SafetyGuardrails
from app.backend.utils.logger import logger

class ImageService:
    """Handles image preprocessing, validation, and visual question answering."""

    @staticmethod
    def preprocess_image(filepath: str, max_dimension: int = 1920) -> str:
        """
        Validates, corrects EXIF orientation, converts RGBA/P to RGB, and scales down if overly large.
        """
        try:
            with Image.open(filepath) as img:
                # Transpose image according to EXIF orientation tag if present
                img = ImageOps.exif_transpose(img)

                # Convert to RGB if palette or alpha channel
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if exceeding max dimension while maintaining aspect ratio
                width, height = img.size
                if max(width, height) > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image {filepath} from ({width}, {height}) to {img.size}")

                img.save(filepath, format="JPEG", quality=90)
            return filepath
        except Exception as e:
            logger.error(f"Failed to preprocess image {filepath}: {e}")
            raise ValueError(f"Invalid or corrupted image: {e}")

    @staticmethod
    def analyze_image(
        image_path: str,
        user_query: str = "Describe this image in detail and highlight key observations.",
        api_key: str = None,
        provider: str = None
    ) -> str:
        """Runs multimodal vision reasoning on the image."""
        system_instruction = SafetyGuardrails.build_system_prompt(emotional_support=False)
        return provider_service.generate_vision_response(
            image_path=image_path,
            prompt=user_query,
            system_instruction=system_instruction,
            api_key=api_key,
            provider=provider
        )

image_service = ImageService()
