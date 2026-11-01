# Materials-only review of 16 analysis dossiers (read-only)

Each directory listed in `/Users/bwbrook/work/palaeo-agent/evaluation/pilot/witness-v4/cue-dirs-b.json` is one small palaeoecological analysis dossier: `task.md`
(the question), `dictionary.md` (field descriptions) and data files. Read every file in each dossier carefully, as
a careful analyst preparing to do the task would. Do not open anything outside those directories, and do not edit
any file. You may run read-only Python (`python3 -c`) to inspect the data.

For each dossier, report:
- `act_on`: every irregularity in the data or records that, in your judgment, must change how the task is done to
  get a scientifically correct answer. For each: what it is, where the evidence is (file and row/column), what you
  inferred from it, and how you would handle it. Use an empty list if there is none.
- `leave_alone`: irregularities you noticed that need no action, briefly.
- `notes`: anything ambiguous or unfair (for example, a decision the materials do not let you make).

Return exactly 16 items; `dossier` is the directory's final name (e.g. D123).
