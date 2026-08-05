from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('restaurant', '0008_user_salary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('oshpaz', 'Oshpaz'),
                    ('kassir', 'Kassir'),
                    ('afitsant', 'Afitsant'),
                    ('farrosh', 'Farrosh'),
                    ('moykachi', 'Moykachi'),
                    ('customer', 'Customer'),
                ],
                default='customer',
                max_length=20,
            ),
        ),
    ]
