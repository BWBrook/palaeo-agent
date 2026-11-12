"""Synthetic public-API implementation review; no Lake Selina data are read."""

import asyncio
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from mcp import Client, StdioServerParameters
import jsonschema
import palaeo_agent as pa
from palaeo_agent.methods import table_files

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def source(root, rows):
    (root/'input.dat').write_text('.\tA\tB\n'+''.join(f's{i+1}\t{a!r}\t{b!r}\n' for i,(a,b) in enumerate(rows)))
    (root/'levels.csv').write_text('sample_id,depth\n'+''.join(f's{i+1},{i}\n' for i in range(len(rows))))
    return {'method':'coniss','input':str(root/'input.dat'),'metadata':str(root/'levels.csv'),'position_column':'depth',
            'format':'past','orientation':'samples_by_taxa','value_type':'count','transform':'hellinger',
            'missing':'error','empty_samples':'drop'}


def rehash(bundle, name):
    manifest = json.loads((bundle/'manifest.json').read_text())
    data = (bundle/name).read_bytes()
    manifest['files'][name].update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    (bundle/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def tamper(root, kind):
    root.mkdir()
    rows = [[1,2],[0,0],[3,1],[2,2]] if kind=='duplicate_exclusion' else [[1,2],[3,1],[2,2]]
    outcome = pa.run(source(root,rows),root/'runs')
    bundle = Path(outcome['run_dir'])
    original = pa.inspect_run(bundle)
    assert original['status']=='verified'
    result = original['result']
    if kind=='ghost_exclusion':
        result['excluded'].append({'sample_id':'ghost','reason':'empty_sample'})
    elif kind=='duplicate_exclusion':
        result['excluded'].append(dict(result['excluded'][0]))
    else:
        result['warnings'].append({'code':'near_duplicate_labels','message':'Injected unsupported warning role',
                                   'details':{'role':'banana'}})
    (bundle/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    rehash(bundle,'results.json')
    for name,data in table_files(result).items():
        (bundle/name).write_bytes(data)
        rehash(bundle,name)
    try:
        inspected = pa.inspect_run(bundle)
    except pa.AnalysisError as exc:
        return {'case':kind,'inspection':'refused','code':exc.code}
    assert inspected['result']==result
    return {'case':kind,'inspection':inspected['status'],'n_input':result['n_input'],'n':result['n'],
            'excluded':result['excluded'],'warnings':result['warnings']}


def unpack(result):
    assert result.structured_content is not None
    assert json.loads(result.content[0].text)==result.structured_content
    return result.structured_content


def client(root):
    return Client(StdioServerParameters(command=sys.executable,args=['-m','palaeo_agent.mcp_server','--root',str(root)]))


async def live(root):
    root.mkdir()
    request = source(root,[[1,2],[3,1],[2,2]])
    request['input']='input.dat'
    request['metadata']='levels.csv'
    async with client(root) as session:
        assert unpack(await session.call_tool('primer',{}))==pa.primer()
        schema = unpack(await session.call_tool('discover',{'method':'coniss'}))
        assert schema['input_schema']['properties']['method']['const']=='coniss'
        tools = {tool.name:tool for tool in (await session.list_tools()).tools}
        jsonschema.validate({'spec':request},tools['run'].input_schema)
        assert unpack(await session.call_tool('validate',{'spec':request}))['status']=='valid'
        run = unpack(await session.call_tool('run',{'spec':request}))
        inspected = unpack(await session.call_tool('inspect',{'bundle':run['run_dir']}))
        assert inspected['status']=='verified'
        native = pa.inspect_run(root/run['run_dir'])['result']
        field = unpack(await session.call_tool('result',{'bundle':run['run_dir'],'field':'total_dispersion'}))
        assert field['value']==native['total_dispersion']
    async with client(root) as fresh:
        reproduced = unpack(await fresh.call_tool('reproduce',{'bundle':run['run_dir']}))
        assert reproduced['status']=='reproduced' and reproduced['differences']==[]
        assert reproduced['tolerance']=={'rtol':0.0,'atol':0.0}
    return {'advertised_schema_accepts_request':True,'validation':'valid','inspection':'verified',
            'scalar_result_matches_native':True,'fresh_server_reproduction':'reproduced',
            'tolerance':reproduced['tolerance']}


def main():
    discovery = pa.discover()
    encoded = json.dumps(discovery)
    prefix_length = len(encoded[:encoded.index('"methods"')])
    assert prefix_length<3072
    details = {method['id']:method for method in discovery['methods']}
    with tempfile.TemporaryDirectory(prefix='s14-public-review-') as temp:
        root = Path(temp)
        cases = [tamper(root/kind,kind) for kind in ('ghost_exclusion','duplicate_exclusion','warning_role')]
        mcp = asyncio.run(live(root/'live'))
        tiny = root/'tiny'; tiny.mkdir()
        request = source(tiny,[[5e-324,1e-323],[1e-323,5e-324],[5e-324,5e-324]])
        request['value_type']='abundance'
        outcome = pa.run(request,tiny/'runs')
        assert pa.inspect_run(outcome['run_dir'])['status']=='verified'
    receipt = {'reviewed_commit':'8b0254d','primer_sha256':pa.primer()['sha256'],
        'scope':'Synthetic public-API and live-MCP checks only; no core data or new scientific application outputs',
        'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'engine_sha256':hashlib.sha256((ROOT/'src/palaeo_agent/coniss.py').read_bytes()).hexdigest(),
        'tamper_cases':cases,'live_mcp':mcp,'compact_discovery_prefix_characters':prefix_length,
        'full_schema_warning_codes':{method:code in json.dumps(details[method]) for method,code in
                                    [('rma','repeated_pairs'),('community','identical_samples')]},
        'subnormal_raw_abundance_input_accepted':True}
    r_path = Path('/private/tmp/s14-r-recheck.json')
    if r_path.exists():
        receipt['rioja_reference_byte_identical'] = r_path.read_bytes()==(ROOT/'references/r/coniss-reference.json').read_bytes()
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
