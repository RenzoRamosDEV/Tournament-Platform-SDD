import os

MUTATION_TARGETS = {
    "app/core/models.py",
    "app/core/serializers.py",
    "app/core/views.py",
}

# KNOWN LIMITATION: mutmut v3 generates mutant IDs from file paths (e.g.
# "app.core.views.*") but pytest-cov records coverage under module names
# (e.g. "core.views.*") because pytest.ini sets `pythonpath = app`.
# This key mismatch causes all mutants to show "no tests" (🫥) even though
# coverage for the targeted files is 100%.
#
# Fix: align file-path prefix with Python import prefix — either move source
# out of app/ or configure mutmut with a source_root that strips the prefix.
# Until then, verify mutation quality via 100% line coverage (pytest --cov).


def pre_mutation(context):
    rel = os.path.relpath(context.filename)
    if rel not in MUTATION_TARGETS:
        context.skip = True
