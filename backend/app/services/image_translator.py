"""Image text extraction / translation service.

MVP placeholder that returns a sentinel string for each image.
Infrastructure is ready for future integration with a vision model
(e.g. Ollama vision, Claude Vision).
"""

from __future__ import annotations

from app.services.image_extractor import ImageData


_PLACEHOLDER_TEXT = "[Image text: requires vision model]"


class ImageTranslatorService:
    """Placeholder service for extracting text from images.

    In the MVP this service returns a fixed placeholder string for every
    image.  Future iterations will call an external vision model to
    perform OCR / image captioning and return the extracted text.
    """

    async def process_image(self, image: ImageData) -> str:
        """Process a single image and return its extracted text.

        Args:
            image: Image data extracted from the document.

        Returns:
            Extracted text from the image, or a placeholder string.
        """
        # TODO: Integrate with vision model (e.g. Ollama llava,
        #       Claude Vision, or a dedicated OCR engine).
        return _PLACEHOLDER_TEXT

    async def process_images(self, images: list[ImageData]) -> list[str]:
        """Process a list of images and return extracted texts.

        Args:
            images: List of ImageData objects.

        Returns:
            List of extracted text strings, one per image.
        """
        results: list[str] = []
        for image in images:
            text = await self.process_image(image)
            results.append(text)
        return results
