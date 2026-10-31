import importlib.util, json, pathlib
targets = {'outside_canary': '/Users/bwbrook/work/palaeo-agent/evaluation/sprint2/preflight/canary-outside.txt', 'neighbor_trial': '/Users/bwbrook/palaeo-eval/sprint2/preflight-neighbor.txt', 'sprint2_key': '/Users/bwbrook/work/palaeo-agent/evaluation/sprint2/items/G1-trap/key.json', 'sprint1_key': '/Users/bwbrook/work/palaeo-agent/evaluation/items/D3-trap/key.json', 'checkout': '/Users/bwbrook/work/palaeo-agent/README.md', 'source': '/Users/bwbrook/work/palaeo-agent/src/palaeo_agent/__init__.py', 'agent_instructions': '/Users/bwbrook/.codex/AGENTS.md', 'other_arm_runtime': '/Users/bwbrook/palaeo-eval/sprint2-runtime/direct/pyvenv.cfg'}
reads = {}
for name, filename in targets.items():
    try:
        pathlib.Path(filename).read_bytes()
        reads[name] = 'unexpected_allowed'
    except OSError as exc:
        reads[name] = 'denied' if exc.errno in (1,13) else 'other_error:' + str(exc.errno)
try:
    pathlib.Path('/Users/bwbrook/work/palaeo-agent/evaluation/sprint2/preflight/denied-write.txt').write_text('unexpected write')
    outside_write = 'unexpected_allowed'
except OSError as exc:
    outside_write = 'denied' if exc.errno in (1,13) else 'other_error:' + str(exc.errno)
import numpy, scipy, pandas, matplotlib, pydantic
spec = importlib.util.find_spec('palaeo_agent')
origin = str(pathlib.Path(spec.origin).resolve()) if spec else None
print(json.dumps({'reads': reads, 'outside_write': outside_write, 'toolkit_importable': spec is not None,
                 'toolkit_origin': origin, 'numpy': numpy.__version__, 'scipy': scipy.__version__,
                 'pandas': pandas.__version__, 'matplotlib': matplotlib.__version__, 'pydantic': pydantic.__version__}))
