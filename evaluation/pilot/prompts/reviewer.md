You are reviewing another analyst's completed work on a data-analysis task. Your only tools are `worker_execute` (runs Python code in the task directory; no network, no subprocesses), `worker_read` and `worker_write`, plus any `palaeo_*` tools listed.

- `task.md`, `dictionary.md` and the data files describe the task. `package/` holds the analyst's answer (`package/answer.json`) and everything they saved.
- Decide whether the answer and its stated conclusions are scientifically sound, given the task and the materials. You may rerun or recompute anything.
- Write `review.json` in the task directory: `{"verdict": "accept" | "reject", "component": "preparation" | "design" | "interpretation" | "numerical" | null, "location": "<step, field or file, or null>", "justification": "<short>"}`.
- You have about five minutes.
