import os
import pytest
from PIL import Image
from app.backend.services.image_service import image_service
from app.backend.services.audio_service import audio_service
from app.backend.core.security import SecurityValidator
from app.backend.utils.file_storage import FileStorageManager

@pytest.mark.asyncio
async def test_audio_speech_synthesis():
    text = "Hello, this is a test speech synthesis from your multimodal companion."
    audio_id, audio_path = await audio_service.synthesize_speech(text)
    assert os.path.exists(audio_path)
    assert os.path.getsize(audio_path) > 0
    # Clean up
    FileStorageManager.delete_file(audio_path)

def test_image_preprocessing():
    # Create test image
    img = Image.new("RGB", (2500, 1800), color=(124, 58, 237))
    temp_path = "app/storage/images/test_preprocess.jpg"
    img.save(temp_path, format="JPEG")

    # Preprocess
    processed_path = image_service.preprocess_image(temp_path, max_dimension=1200)
    with Image.open(processed_path) as res_img:
        w, h = res_img.size
        assert max(w, h) <= 1200

    # Cleanup
    FileStorageManager.delete_file(temp_path)

def test_security_file_validation():
    # Valid PNG header
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    valid, ext = SecurityValidator.validate_image("photo.png", png_bytes)
    assert valid is True
    assert ext == "png"

    # Invalid extension
    with pytest.raises(Exception):
        SecurityValidator.validate_image("script.exe", b"MZ" + b"\x00" * 50)
