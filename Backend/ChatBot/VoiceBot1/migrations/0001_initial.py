# Generated by Django 5.1.7 on 2025-03-25 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_input', models.TextField()),
                ('bot_response', models.TextField()),
                ('audio_response', models.FileField(null=True, upload_to='audio_responses/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
