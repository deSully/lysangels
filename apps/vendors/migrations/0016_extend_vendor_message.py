# Generated manually on 2026-06-09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("vendors", "0015_add_vendor_message"),
    ]

    operations = [
        # VendorProfile : ajout email
        migrations.AddField(
            model_name="vendorprofile",
            name="email",
            field=models.EmailField(blank=True, verbose_name="Email"),
        ),
        # VendorMessage : application devient nullable
        migrations.AlterField(
            model_name="vendormessage",
            name="application",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="vendors.vendorapplication",
                verbose_name="Candidature",
            ),
        ),
        # VendorMessage : ajout FK vendor_profile
        migrations.AddField(
            model_name="vendormessage",
            name="vendor_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="vendors.vendorprofile",
                verbose_name="Prestataire",
            ),
        ),
        # VendorMessage : ajout recipient_email + recipient_name
        migrations.AddField(
            model_name="vendormessage",
            name="recipient_email",
            field=models.EmailField(blank=True, verbose_name="Email destinataire"),
        ),
        migrations.AddField(
            model_name="vendormessage",
            name="recipient_name",
            field=models.CharField(blank=True, max_length=200, verbose_name="Nom destinataire"),
        ),
    ]
