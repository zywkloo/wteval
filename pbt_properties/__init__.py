"""Property catalogs for the wteval PBT runner.

Each catalog module exports ``properties()`` returning a list of
``{"name", "shape", "failure"}`` dicts. Catalogs here target wtcraft's
deterministic oracle (the policy-evaluator), recombining its committed contract
fixtures into generated inputs.
"""
