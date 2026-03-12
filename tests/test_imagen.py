"""Tests for the Imagen image generation service."""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.config import IMAGEN_MODEL


@patch("backend.services.imagen.client")
def test_generate_image_writes_bytes(mock_client):
    """generate_image should write returned image bytes to output_path."""
    fake_bytes = b"\x89PNG\r\n\x1a\nfake-image-data"

    mock_image = MagicMock()
    mock_image.image.image_bytes = fake_bytes

    mock_response = MagicMock()
    mock_response.generated_images = [mock_image]
    mock_client.models.generate_images.return_value = mock_response

    from backend.services.imagen import generate_image

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "test_output.png"
        result = generate_image("a sunset over mountains", str(out))

        assert result == str(out)
        assert out.exists()
        assert out.read_bytes() == fake_bytes

    mock_client.models.generate_images.assert_called_once_with(
        model=IMAGEN_MODEL,
        prompt="a sunset over mountains",
        config={"number_of_images": 1},
    )


@patch("backend.services.imagen.client")
def test_generate_image_raises_on_empty_response(mock_client):
    """generate_image should raise RuntimeError when Imagen returns no images."""
    mock_response = MagicMock()
    mock_response.generated_images = []
    mock_client.models.generate_images.return_value = mock_response

    from backend.services.imagen import generate_image

    with pytest.raises(RuntimeError, match="Imagen returned no images"):
        generate_image("a prompt that fails", "/tmp/nope.png")


@patch("backend.services.imagen.client")
def test_generate_image_raises_on_none_response(mock_client):
    """generate_image should raise RuntimeError when generated_images is None."""
    mock_response = MagicMock()
    mock_response.generated_images = None
    mock_client.models.generate_images.return_value = mock_response

    from backend.services.imagen import generate_image

    with pytest.raises(RuntimeError, match="Imagen returned no images"):
        generate_image("another failing prompt", "/tmp/nope.png")
