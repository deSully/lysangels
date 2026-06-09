# Generated manually on 2026-06-09

from django.db import migrations, models
import django.db.models.deletion
import apps.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ("vendors", "0014_add_logo_to_vendor_application"),
    ]

    operations = [
        migrations.CreateModel(
            name="VendorMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="vendors.vendorapplication",
                        verbose_name="Candidature",
                    ),
                ),
                ("subject", models.CharField(max_length=200, verbose_name="Objet")),
                ("body", models.TextField(verbose_name="Message")),
                ("reply_body", models.TextField(blank=True, verbose_name="Réponse du prestataire")),
                (
                    "reply_image_1",
                    models.ImageField(
                        blank=True, null=True,
                        upload_to="vendor_messages/",
                        validators=[apps.core.validators.validate_image_file],
                        verbose_name="Photo jointe 1",
                    ),
                ),
                (
                    "reply_image_2",
                    models.ImageField(
                        blank=True, null=True,
                        upload_to="vendor_messages/",
                        validators=[apps.core.validators.validate_image_file],
                        verbose_name="Photo jointe 2",
                    ),
                ),
                (
                    "reply_image_3",
                    models.ImageField(
                        blank=True, null=True,
                        upload_to="vendor_messages/",
                        validators=[apps.core.validators.validate_image_file],
                        verbose_name="Photo jointe 3",
                    ),
                ),
                ("token", models.CharField(max_length=200, unique=True, verbose_name="Token de réponse")),
                ("token_used", models.BooleanField(default=False, verbose_name="Lien utilisé")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("sent", "Envoyé"),
                            ("replied", "Répondu"),
                            ("read", "Lu"),
                            ("processed", "Traité"),
                        ],
                        db_index=True,
                        default="sent",
                        max_length=20,
                        verbose_name="Statut",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("replied_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de réponse")),
            ],
            options={
                "verbose_name": "Message prestataire",
                "verbose_name_plural": "Messages prestataires",
                "ordering": ["-created_at"],
            },
        ),
    ]
