from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0016_add_contact_view_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nom complet')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('whatsapp', models.CharField(max_length=30, verbose_name='WhatsApp')),
                ('city', models.CharField(max_length=100, verbose_name='Ville')),
                ('description', models.TextField(verbose_name="Description de l'activité")),
                ('instagram', models.CharField(blank=True, max_length=200, verbose_name='Instagram')),
                ('facebook', models.CharField(blank=True, max_length=200, verbose_name='Facebook')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente'),
                        ('contacted', 'Contacté'),
                        ('approved', 'Approuvé'),
                        ('rejected', 'Refusé'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20,
                    verbose_name='Statut',
                )),
                ('admin_notes', models.TextField(blank=True, verbose_name='Notes admin')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('service_types', models.ManyToManyField(
                    blank=True,
                    related_name='applications',
                    to='vendors.servicetype',
                    verbose_name='Types de prestation',
                )),
            ],
            options={
                'verbose_name': 'Candidature prestataire',
                'verbose_name_plural': 'Candidatures prestataires',
                'ordering': ['-created_at'],
            },
        ),
    ]
