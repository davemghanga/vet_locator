# Generated by Django 5.1.6 on 2025-02-19 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dogprofile',
            name='image',
            field=models.ImageField(default='dog_profiles/default.jpeg', upload_to='dog_profiles/'),
        ),
    ]
