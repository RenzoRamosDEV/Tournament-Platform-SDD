import os

MUTATION_TARGETS = {
    "app/apps/users/models.py",
    "app/apps/teams/models.py",
    "app/apps/tournaments/models.py",
    "app/apps/users/views.py",
    "app/apps/teams/views.py",
    "app/apps/tournaments/views.py",
    "app/events/producer.py",
    "app/events/consumer_base.py",
    "app/consumers/ranking_consumer.py",
    "app/consumers/notification_consumer.py",
    "app/consumers/log_consumer.py",
}


def pre_mutation(context):
    rel = os.path.relpath(context.filename)
    if rel not in MUTATION_TARGETS:
        context.skip = True
