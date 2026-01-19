from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='admin_event_help',
            field=models.BooleanField(default=False, verbose_name="Accompagnement par l'admin event", help_text="Si coché, l'admin event est l'interlocuteur unique pour ce projet."),
        ),
    ]
