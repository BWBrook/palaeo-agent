# Materials-only identifiability review of 11 analysis dossiers (read-only)

Each directory listed in `/Users/bwbrook/work/palaeo-agent/evaluation/pilot/witness-v4/r3-dirs.json` is one palaeoecological analysis dossier: `task.md` (the
question), `dictionary.md` (field descriptions) and data files. Read every file carefully, as a careful analyst
would before doing the task. Do not open anything outside those directories and do not edit any file. You may run
read-only Python (`python3 -c`).

For each dossier report:
- `determined`: is the requested quantity uniquely determined by the materials (up to rounding)? yes / no / uncertain.
- `handling`: how you would compute it (or why it cannot be computed, and what you would report instead).
- `defensible_alternatives`: every OTHER handling a careful scientist could defend that would give different
  numbers. Empty list if none.
- `act_on`: irregularities that must change how the task is done.
- `notes`: anything ambiguous, unfair or inconsistent.

Return exactly 11 items; `dossier` is the directory's final name (e.g. E123).
