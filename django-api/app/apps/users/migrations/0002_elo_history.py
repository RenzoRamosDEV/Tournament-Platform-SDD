import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('tournaments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EloHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('elo_before', models.IntegerField()),
                ('elo_after', models.IntegerField()),
                ('changed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('match', models.ForeignKey(db_column='match_id', on_delete=django.db.models.deletion.CASCADE, to='tournaments.match')),
            ],
            options={
                'db_table': 'elo_history',
            },
        ),
    ]
