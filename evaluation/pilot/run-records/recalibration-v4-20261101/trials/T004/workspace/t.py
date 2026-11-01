import json, shutil, numpy as np, palaeo_agent
spec = json.load(open("specs/study.json"))
shutil.rmtree("study_out", ignore_errors=True)
r = palaeo_agent.run_study(spec, "study_out", base_dir="specs")
print(r if not hasattr(r,"model_dump") else list(r.model_dump())[:10])
