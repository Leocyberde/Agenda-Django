
# Generated migration for changing photo field from URLField to ImageField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0013_salon_cancellation_fee_percentage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salon',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='salon_photos/', verbose_name='Foto do Salão'),
        ),
    ]
