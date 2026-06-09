# Generated manually on 2026-06-09

from django.db import migrations, models
import apps.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("vendors", "0013_add_vendor_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="vendorapplication",
            name="logo",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="applications/logos/",
                validators=[apps.core.validators.validate_image_file],
                verbose_name="Logo / photo de profil",
            ),
        ),
    ]
