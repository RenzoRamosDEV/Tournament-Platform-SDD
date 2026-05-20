import datetime
import sys
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import EloHistory, Match, Team, TeamMember, Tournament, TournamentTeam, User


class Command(BaseCommand):
    help = "Populate the database with development seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all core data before seeding (only allowed when DEBUG=True).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            if not settings.DEBUG:
                self.stdout.write("--clear is not allowed outside DEBUG mode.")
                sys.exit(1)
            self._clear()

        self._seed()
        self.stdout.write("Seed data created successfully.")

    def _clear(self):
        EloHistory.objects.all().delete()
        Match.objects.all().delete()
        TournamentTeam.objects.all().delete()
        Tournament.objects.all().delete()
        TeamMember.objects.all().delete()
        Team.objects.all().delete()
        User.objects.all().delete()

    def _seed(self):
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@tournament.local", "role": "admin", "elo": 1000},
        )
        admin.set_password("admin1234")
        admin.save(update_fields=["password"])

        organizers = []
        for i in range(1, 4):
            org, _ = User.objects.get_or_create(
                username=f"organizer{i}",
                defaults={"email": f"organizer{i}@tournament.local", "role": "organizer", "elo": 1000},
            )
            org.set_password("password")
            org.save(update_fields=["password"])
            organizers.append(org)

        players = []
        for i in range(1, 17):
            player, _ = User.objects.get_or_create(
                username=f"player{i}",
                defaults={"email": f"player{i}@tournament.local", "role": "player", "elo": 1000},
            )
            player.set_password("password")
            player.save(update_fields=["password"])
            players.append(player)

        teams = []
        for i in range(1, 7):
            owner = organizers[(i - 1) % len(organizers)]
            team, _ = Team.objects.get_or_create(name=f"Team {i}", defaults={"owner": owner})
            teams.append(team)

        for idx, player in enumerate(players):
            team = teams[idx % len(teams)]
            TeamMember.objects.get_or_create(user=player, team=team)

        finished_t, _ = Tournament.objects.get_or_create(
            name="Spring Cup 2025",
            defaults={
                "status": "finished",
                "format": "single_elimination",
                "max_teams": 4,
                "start_date": datetime.date(2025, 3, 1),
                "end_date": datetime.date(2025, 3, 15),
                "created_by": organizers[0],
            },
        )
        ongoing_t, _ = Tournament.objects.get_or_create(
            name="Summer League 2026",
            defaults={
                "status": "ongoing",
                "format": "round_robin",
                "max_teams": 4,
                "start_date": datetime.date(2026, 6, 1),
                "end_date": datetime.date(2026, 6, 30),
                "created_by": organizers[1],
            },
        )
        open_t, _ = Tournament.objects.get_or_create(
            name="Autumn Championship 2026",
            defaults={
                "status": "open",
                "format": "single_elimination",
                "max_teams": 8,
                "start_date": datetime.date(2026, 9, 1),
                "end_date": datetime.date(2026, 9, 20),
                "created_by": organizers[2],
            },
        )

        for team in teams[:4]:
            TournamentTeam.objects.get_or_create(tournament=finished_t, team=team)
        for team in teams[:4]:
            TournamentTeam.objects.get_or_create(tournament=ongoing_t, team=team)
        for team in teams:
            TournamentTeam.objects.get_or_create(tournament=open_t, team=team)

        finished_matches_data = [
            (teams[0], teams[1], teams[0], finished_t),
            (teams[2], teams[3], teams[2], finished_t),
            (teams[0], teams[2], teams[0], finished_t),
            (teams[0], teams[1], teams[1], ongoing_t),
            (teams[2], teams[3], teams[3], ongoing_t),
        ]
        scheduled_matches_data = [
            (teams[1], teams[2], ongoing_t),
            (teams[0], teams[3], ongoing_t),
            (teams[0], teams[1], open_t),
            (teams[2], teams[3], open_t),
            (teams[4], teams[5], open_t),
            (teams[0], teams[4], open_t),
            (teams[1], teams[5], open_t),
        ]

        for team_a, team_b, winner, tournament in finished_matches_data:
            match, created = Match.objects.get_or_create(
                tournament=tournament,
                team_a=team_a,
                team_b=team_b,
                defaults={
                    "winner_team": winner,
                    "score_a": 2 if winner == team_a else 0,
                    "score_b": 2 if winner == team_b else 0,
                    "status": "finished",
                    "played_at": datetime.datetime(2025, 3, 5, 14, 0, 0, tzinfo=ZoneInfo("UTC")),
                },
            )
            if created:
                team_a_members = list(TeamMember.objects.filter(team=team_a).select_related("user"))
                team_b_members = list(TeamMember.objects.filter(team=team_b).select_related("user"))
                for member in team_a_members + team_b_members:
                    delta = 20 if member.team == winner else -20
                    EloHistory.objects.get_or_create(
                        user=member.user,
                        match=match,
                        defaults={
                            "elo_before": member.user.elo,
                            "elo_after": member.user.elo + delta,
                        },
                    )

        for team_a, team_b, tournament in scheduled_matches_data:
            Match.objects.get_or_create(
                tournament=tournament,
                team_a=team_a,
                team_b=team_b,
                defaults={"status": "scheduled"},
            )
