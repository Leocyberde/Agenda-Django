
# Generated migration for cancellation fee details

from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('salons', '0014_alter_salon_photo_to_imagefield'),
        ('appointments', '0007_remove_appointment_unique_employee_appointment_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cancellationfee',
            name='cancelled_at',
            field=models.DateTimeField(default=timezone.now, verbose_name='Data e Hora do Cancelamento'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cancellationfee',
            name='cancelled_by_employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='salons.employee', verbose_name='Funcionário do Agendamento'),
        ),
    ]
