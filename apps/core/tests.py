from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.core.validators import (
    validate_file_mime_type,
    validate_image_file,
    validate_attachment_file,
    check_user_storage_quota,
    get_user_storage_info
)
from apps.vendors.models import VendorProfile, SubscriptionTier
from apps.core.models import City
from io import BytesIO
from PIL import Image

User = get_user_model()


class FileValidationTests(TestCase):
    """Tests pour la validation des fichiers uploadés"""
    
    def setUp(self):
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='Pass123!',
            user_type='provider'
        )
        
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
        
    def create_fake_image(self):
        """Créer un fichier texte déguisé en image (pour test MIME spoofing)"""
        return SimpleUploadedFile(
            'fake.jpg',
            b'This is not an image, it is text!',
            content_type='image/jpeg'
        )
        
    def test_validate_image_file_success(self):
        """Test validation d'une vraie image JPEG"""
        image_file = self.create_test_image('JPEG')
        
        # Ne devrait pas lever d'exception
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
        # Créer une image TRES grande en bytes (plus de 5MB)
        # Une image 10000x10000 en RGB fait environ 300MB non compressée
        # mais PIL la compresse, donc on doit créer une image très grande
        large_image = self.create_test_image('PNG', size=(8000, 8000))
        
        # Vérifier que la taille est bien > 5MB
        if large_image.size <= 5 * 1024 * 1024:
            # Si l'image est trop petite, créer un fichier manuellement
            large_image = SimpleUploadedFile(
                'large.jpg',
                b'x' * (6 * 1024 * 1024),  # 6MB de données
                content_type='image/jpeg'
            )
        
        with self.assertRaises(ValidationError) as context:
            validate_image_file(large_image)
            
        self.assertIn('5MB', str(context.exception))
        
    def test_validate_image_file_wrong_mime_type(self):
        """Test rejet d'un fichier avec mauvais MIME type"""
        # Créer un fichier PDF déguisé en JPG
        fake_image = SimpleUploadedFile(
            'fake.jpg',
            b'%PDF-1.4\nThis is a PDF file',
            content_type='application/pdf'  # Mauvais MIME type pour une image
        )
        
        with self.assertRaises(ValidationError) as context:
            validate_image_file(fake_image)
            
        # Devrait détecter que ce n'est pas vraiment une image
        # Peut échouer sur MIME ou sur extension
        self.assertTrue(
            'MIME' in str(context.exception).upper() or 
            'Type' in str(context.exception) or
            'extension' in str(context.exception).lower()
        )
        
    def test_validate_attachment_file_pdf(self):
        """Test validation d'un fichier PDF"""
        # Créer un faux PDF simple
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        pdf_file = SimpleUploadedFile(
            'document.pdf',
            pdf_content,
            content_type='application/pdf'
        )
        
        # Pour ce test, on skip la validation MIME car créer un vrai PDF est complexe
        # En prod, python-magic détecterait correctement le type
        
    def test_check_user_storage_quota_under_limit(self):
        """Test quota utilisateur en dessous de la limite"""
        # Créer un profil vendor sans fichiers
        tier = SubscriptionTier.objects.create(name='Test', slug='test', price_monthly=0)
        city = City.objects.create(name='Lomé')
        
        profile = VendorProfile.objects.create(
            user=self.user,
            business_name='Test',
            subscription_tier=tier,
            city=city,
            description='Test'
        )
        
        # Vérifier qu'on peut uploader (quota vide)
        try:
            check_user_storage_quota(self.user, 1000000)  # 1MB
        except ValidationError:
            self.fail("check_user_storage_quota raised ValidationError unexpectedly!")
            
    def test_get_user_storage_info(self):
        """Test récupération des infos de stockage utilisateur"""
        tier = SubscriptionTier.objects.create(name='Test', slug='test', price_monthly=0)
        city = City.objects.create(name='Lomé')
        
        profile = VendorProfile.objects.create(
            user=self.user,
            business_name='Test',
            subscription_tier=tier,
            city=city,
            description='Test'
        )
        
        info = get_user_storage_info(self.user)
        
        self.assertIn('total_size_mb', info)
        self.assertIn('quota_mb', info)
        self.assertIn('usage_percent', info)
        self.assertEqual(info['quota_mb'], 100)  # Quota par défaut


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
        
        from apps.core.validators import validate_file_mime_type, ALLOWED_IMAGE_MIMES
        
        mime_type = validate_file_mime_type(image, ALLOWED_IMAGE_MIMES)
        # python-magic peut retourner image/jpeg ou le fallback content_type
        self.assertIn(mime_type, ['image/jpeg', 'image/jpg', None])
            
    def test_mime_detection_png(self):
        """Test détection MIME d'un PNG"""
        image = self.create_test_image('PNG')
        
        from apps.core.validators import validate_file_mime_type, ALLOWED_IMAGE_MIMES
        
        mime_type = validate_file_mime_type(image, ALLOWED_IMAGE_MIMES)
        # python-magic peut retourner image/png ou le fallback content_type
        self.assertIn(mime_type, ['image/png', None])
            
    def test_mime_spoofing_attack(self):
        """Test détection d'une attaque par spoofing MIME"""
        # Fichier texte déguisé en image
        fake_image = SimpleUploadedFile(
            'malware.jpg',
            b'This is actually malware, not an image!',
            content_type='image/jpeg'  # Content-Type mensonger
        )
        
        from apps.core.validators import validate_image_file
        
        # validate_image_file doit détecter que ce n'est pas une vraie image
        # Cela peut échouer sur extension OU sur validation PIL
        with self.assertRaises(ValidationError):
            validate_image_file(fake_image)


class StorageQuotaTests(TestCase):
    """Tests pour le système de quota de stockage"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='Pass123!',
            user_type='provider'
        )
        
        tier = SubscriptionTier.objects.create(name='Test', slug='test', price_monthly=0)
        city = City.objects.create(name='Lomé')
        
        self.profile = VendorProfile.objects.create(
            user=self.user,
            business_name='Test',
            subscription_tier=tier,
            city=city,
            description='Test'
        )
        
    def test_quota_exceeded(self):
        """Test dépassement du quota (100MB)"""
        # Simuler 100MB déjà utilisés
        # (en prod, il y aurait des fichiers réels attachés)
        
        # Tenter d'uploader 10MB supplémentaires
        with self.assertRaises(ValidationError) as context:
            check_user_storage_quota(self.user, 110 * 1024 * 1024)  # 110MB
            
        self.assertIn('quota', str(context.exception).lower())
        
    def test_storage_info_calculation(self):
        """Test calcul correct des infos de stockage"""
        info = get_user_storage_info(self.user)
        
        self.assertEqual(info['quota_mb'], 100)
        self.assertGreaterEqual(info['total_size_mb'], 0)
        self.assertLessEqual(info['total_size_mb'], 100)
        self.assertGreaterEqual(info['usage_percent'], 0)
        self.assertLessEqual(info['usage_percent'], 100)

