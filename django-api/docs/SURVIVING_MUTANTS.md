# Surviving Mutants — Justification

**Final score: 57/61 = 93.4%**

The 4 surviving mutants are all confirmed equivalent mutants that cannot be killed by tests due to mutmut v3's trampoline architecture or single-database test environment.

## `core.models.UserManager.create_user`

### mutmut_1 & mutmut_2 — Default `role` parameter
**Mutation:** `role="player"` → `role="XXplayerXX"` / `role="PLAYER"`

**Why it survives:** mutmut v3 wraps functions in a trampoline that captures call arguments positionally. When `create_user(username, password)` is called (no explicit role), the trampoline captures `role="player"` from the ORIGINAL signature's default and passes it as a positional argument to the mutated function. The mutated default value is never evaluated.

**Verdict:** Equivalent mutant — untestable via black-box tests.

### mutmut_3 — Default `elo` parameter
**Mutation:** `elo=1000` → `elo=1001`

**Why it survives:** Same trampoline issue as above. The original default `1000` is captured and passed positionally; the mutated `1001` is unreachable.

**Verdict:** Equivalent mutant — untestable via black-box tests.

### mutmut_13 — `save(using=self._db)` → `save(using=None)`
**Mutation:** `user.save(using=None)` instead of `user.save(using=self._db)`

**Why it survives:** In a single-database Django setup (both test and production), `using=None` and `using=self._db` both resolve to the same `default` database alias. The behavior is identical.

**Verdict:** Equivalent mutant in single-database environments.
