import os

def pre_mutation(context):
    rel = os.path.relpath(context.filename)
    if rel not in ("app/core/models.py", "app/core/serializers.py"):
        context.skip = True
