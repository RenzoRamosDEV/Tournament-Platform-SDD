import os

MUTATION_TARGETS = {
    "app/apps/users/models.py",
    "app/apps/teams/models.py",
    "app/apps/tournaments/models.py",
    "app/apps/users/views.py",
    "app/apps/teams/views.py",
    "app/apps/tournaments/views.py",
}


def pre_mutation(context):
    rel = os.path.relpath(context.filename)
    if rel not in MUTATION_TARGETS:
        context.skip = True
