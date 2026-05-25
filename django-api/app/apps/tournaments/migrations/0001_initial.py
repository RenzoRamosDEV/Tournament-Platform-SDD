import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_a', models.IntegerField(default=0)),
                ('score_b', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('scheduled', 'scheduled'), ('ongoing', 'ongoing'), ('finished', 'finished')], default='scheduled', max_length=10)),
                ('played_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'matches',
            },
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('status', models.CharField(choices=[('draft', 'draft'), ('open', 'open'), ('ongoing', 'ongoing'), ('finished', 'finished')], default='draft', max_length=10)),
                ('format', models.CharField(choices=[('single_elimination', 'single_elimination'), ('round_robin', 'round_robin')], max_length=20)),
                ('max_teams', models.PositiveIntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('created_by', models.ForeignKey(db_column='created_by_id', on_delete=django.db.models.deletion.PROTECT, related_name='created_tournaments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tournaments',
            },
        ),
        migrations.AddField(
            model_name='match',
            name='tournament',
            field=models.ForeignKey(db_column='tournament_id', on_delete=django.db.models.deletion.CASCADE, related_name='matches', to='tournaments.tournament'),
        ),
        migrations.AddField(
            model_name='match',
            name='team_a',
            field=models.ForeignKey(db_column='team_a_id', on_delete=django.db.models.deletion.PROTECT, related_name='matches_as_a', to='teams.team'),
        ),
        migrations.AddField(
            model_name='match',
            name='team_b',
            field=models.ForeignKey(db_column='team_b_id', on_delete=django.db.models.deletion.PROTECT, related_name='matches_as_b', to='teams.team'),
        ),
        migrations.AddField(
            model_name='match',
            name='winner_team',
            field=models.ForeignKey(blank=True, db_column='winner_team_id', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='won_matches', to='teams.team'),
        ),
        migrations.CreateModel(
            name='TournamentTeam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('team', models.ForeignKey(db_column='team_id', on_delete=django.db.models.deletion.CASCADE, to='teams.team')),
                ('tournament', models.ForeignKey(db_column='tournament_id', on_delete=django.db.models.deletion.CASCADE, to='tournaments.tournament')),
            ],
            options={
                'db_table': 'tournament_teams',
            },
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(condition=models.Q(('status__in', ['draft', 'open', 'ongoing', 'finished'])), name='tournaments_status_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(condition=models.Q(('format__in', ['single_elimination', 'round_robin'])), name='tournaments_format_valid'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(condition=models.Q(('max_teams__gt', 0)), name='tournaments_max_teams_positive'),
        ),
        migrations.AddConstraint(
            model_name='tournament',
            constraint=models.CheckConstraint(condition=models.Q(('end_date__gte', models.F('start_date'))), name='tournaments_end_date_gte_start_date'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['tournament'], name='matches_tournament_idx'),
        ),
        migrations.AddIndex(
            model_name='match',
            index=models.Index(fields=['played_at'], name='matches_played_at_idx'),
        ),
        migrations.AddConstraint(
            model_name='tournamentteam',
            constraint=models.UniqueConstraint(fields=('tournament', 'team'), name='tournament_teams_pk'),
        ),
    ]
