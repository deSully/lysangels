from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.validators import (
    validate_file_mime_type,
    validate_image_file,
    ALLOWED_IMAGE_MIMES,
)
from io import BytesIO
from PIL import Image


class FileValidationTests(TestCase):
    """Tests pour la validation des fichiers uploadés"""

    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Créer une image de test en mémoire"""
        image = Image.new('RGB', size, color='red')
        file = BytesIO()
        image.save(file, format=format)
        file.seek(0)
        return SimpleUploadedFile(
            f'test.{format.lower()}',
            file.read(),
            content_type=f'image/{format.lower()}'
        )

    def test_validate_image_file_success(self):
        """Test validation d'une vraie image JPEG"""
        image_file = self.create_test_image('JPEG')
        try:
            validate_image_file(image_file)
        except ValidationError:
            self.fail("validate_image_file raised ValidationError unexpectedly!")

    def test_validate_image_file_png_success(self):
        """Test validation d'une vraie image PNG"""
        image_file = self.create_test_image('PNG')
        try:
            validate_image_file(image_file)
        except ValidationError:
            self.fail("validate_image_file raised ValidationError unexpectedly!")

    def test_validate_image_file_too_large(self):
        """Test rejet d'une image trop grande (> 5MB)"""
        large_image = SimpleUploadedFile(
            'large.jpg',
            b'x' * (6 * 1024 * 1024),  # 6MB de données
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError) as context:
            validate_image_file(large_image)
        self.assertIn('5MB', str(context.exception))

    def test_validate_image_file_wrong_extension(self):
        """Test rejet d'un fichier avec mauvaise extension"""
        fake_image = SimpleUploadedFile(
            'document.pdf',
            b'%PDF-1.4\nThis is a PDF file',
            content_type='application/pdf'
        )
        with self.assertRaises(ValidationError):
            validate_image_file(fake_image)


class MIMETypeDetectionTests(TestCase):
    """Tests pour la détection des types MIME"""

    def create_test_image(self, format='JPEG'):
        """Créer une vraie image"""
        image = Image.new('RGB', (50, 50), color='blue')
        file = BytesIO()
        image.save(file, format=format)
        file.seek(0)
        return SimpleUploadedFile(
            f'test.{format.lower()}',
            file.read(),
            content_type=f'image/{format.lower()}'
        )

    def test_mime_detection_jpeg(self):
        """Test détection MIME d'un JPEG"""
        image = self.create_test_image('JPEG')
        mime_type = validate_file_mime_type(image, ALLOWED_IMAGE_MIMES)
        self.assertIn(mime_type, ['image/jpeg', 'image/jpg', None])

    def test_mime_detection_png(self):
        """Test détection MIME d'un PNG"""
        image = self.create_test_image('PNG')
        mime_type = validate_file_mime_type(image, ALLOWED_IMAGE_MIMES)
        self.assertIn(mime_type, ['image/png', None])

    def test_mime_spoofing_attack(self):
        """Test détection d'une attaque par spoofing MIME"""
        fake_image = SimpleUploadedFile(
            'malware.jpg',
            b'This is actually malware, not an image!',
            content_type='image/jpeg'
        )
        with self.assertRaises(ValidationError):
            validate_image_file(fake_image)
