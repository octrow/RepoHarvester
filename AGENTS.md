# Agents: start here

1. `README.md`: what the tool does and its options.
2. `docs/logic-map.md`: how a repository becomes one text file: every step, every branch, the module behind it.
3. `docs/plans/`: work in progress; `2026-11-05-logic-map-fixes.md` lists the known logic gaps.
4. Open bugs, plans and ideas: [PLAN.md](PLAN.md).

Rules:
- Change a step or a branch → update `docs/logic-map.md` in the same commit.
- `test_logic_map.py` fails when a `Module:` line in the map points to a module that is gone.
