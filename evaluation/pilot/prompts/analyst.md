You are doing a data-analysis task. Your only tools are `mcp__worker__worker_execute` (runs Python code in the task directory, with numpy, scipy, pandas and matplotlib installed; no network, no subprocesses), `mcp__worker__worker_read` and `mcp__worker__worker_write` (task-directory files, paths relative to it).

- Read `task.md` and `dictionary.md`. The data files are in the same directory.
- Your deliverable is one self-contained script, `analysis.py`, in the task directory. Run as `python analysis.py` from the task directory, with only the supplied files present (plus anything you keep under `specs/`), it must redo the whole analysis from the supplied data and write `answer.json`, which must conform to `answer.schema.json`. Report numbers as computed, without rounding.
- Produce your final `answer.json` by running that script, with `mcp__worker__worker_execute` and the code `import runpy; runpy.run_path("analysis.py", run_name="__main__")`.
- Only `analysis.py` and `specs/` are kept. Everything else you create is treated as regenerable output, and the script will be re-run from a fresh copy of the supplied files.
- You have about ten minutes.
