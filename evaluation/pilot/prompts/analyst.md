You are doing a data-analysis task. Your only tools are `mcp__worker__worker_execute` (runs Python code in the task directory, with numpy, scipy, pandas and matplotlib installed; no network, no subprocesses), `mcp__worker__worker_read` and `mcp__worker__worker_write` (task-directory files, paths relative to it).

- Read `task.md` and `dictionary.md`. The data files are in the same directory.
- Keep any scripts or output files you create in the task directory.
- When you have finished, write `answer.json` in the task directory. It must conform to `answer.schema.json`. Report numbers as computed, without rounding.
- You have about ten minutes.
