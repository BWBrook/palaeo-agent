from pathlib import Path
import asyncio
import hashlib
import json
import shutil
import sys

from mcp import Client, StdioServerParameters
import palaeo_agent as pa


root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=False)
repo = Path(__file__).resolve().parents[3]
source = root / 'download.json'
shutil.copyfile(repo / 'analyses/lake-selina/source/neotoma-52767-download.json', source)
spec = dict(source='download.json', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            datasets='all', units='NISP', elements=['pollen'], ecological_groups=['TRSH', 'UPHE'],
            absent_taxa='zero', row_order='depth')


def unpack(value):
    assert value.structured_content is not None
    assert json.loads(value.content[0].text) == value.structured_content
    return value.structured_content


async def main():
    async with Client(StdioServerParameters(command=sys.executable,
                      args=['-m', 'palaeo_agent.mcp_server', '--root', str(root)])) as client:
        primer = unpack(await client.call_tool('primer', {}))
        tools = await client.list_tools()
        tool = next(t.model_dump(by_alias=True) for t in tools.tools if t.name == 'neotoma_extract')
        result = unpack(await client.call_tool('neotoma_extract', {'spec': spec, 'output': 'live'}))
        assert result['status'] == 'complete'
        bundle = Path(result['bundle'])
        before = unpack(await client.call_tool('neotoma_inspect', {'bundle': str(bundle)}))
        with_method = unpack(await client.call_tool('neotoma_extract',
                           {'spec': {**spec, 'method': 'community'}, 'output': 'invalid-live'}))
        source.unlink()
        after = unpack(await client.call_tool('neotoma_inspect', {'bundle': str(bundle)}))
        repeated = unpack(await client.call_tool('neotoma_reproduce',
                          {'bundle': str(bundle), 'output': 'repeated-live'}))
        outside = unpack(await client.call_tool('neotoma_extract',
                         {'spec': {**spec, 'source': '../outside.json'}, 'output': 'outside'}))
    environment = before['environment']
    manifest = json.loads((bundle / 'manifest.json').read_text())
    receipt = {
        'reviewed_commit': '6f17b50',
        'primer': {k: primer[k] for k in ('version', 'sha256')},
        'live_tool_schema': tool['inputSchema'],
        'valid_call': {'status': result['status'], 'kind': result['kind'],
                       'n_samples': result['n_samples'], 'n_labels': result['n_labels']},
        'call_with_advertised_method': with_method,
        'inspection_before_source_move': before['status'],
        'inspection_after_source_move': after['status'],
        'reproduction': {k: repeated[k] for k in ('status', 'differences', 'environment_identical')},
        'outside_root': {'status': outside['status'], 'code': outside['code']},
        'lockfile_record': environment['lockfile'],
        'lockfile_in_bundle': (bundle / 'uv.lock').exists(),
        'lockfile_in_manifest': 'uv.lock' in manifest['files'],
        'bundle_files': sorted(manifest['files']),
    }
    probes = []
    for name, manifest_value in [('list', []), ('bool_schema', None)]:
        target = root / ('manifest-' + name)
        shutil.copytree(bundle, target)
        path = target / 'manifest.json'
        if manifest_value is None:
            manifest_value = json.loads(path.read_text())
            manifest_value['schema_version'] = True
        path.write_text(json.dumps(manifest_value))
        try:
            probes.append({'case': name, 'status': pa.inspect_neotoma(target)['status']})
        except Exception as exc:
            probes.append({'case': name, 'exception': type(exc).__name__,
                           'code': getattr(exc, 'code', None), 'message': str(exc)})
    target = root / 'manifest-link'
    shutil.copytree(bundle, target)
    path = target / 'manifest.json'
    external = root / 'external-manifest.json'
    shutil.move(path, external)
    path.symlink_to(external)
    try:
        probes.append({'case': 'external_manifest_symlink', 'status': pa.inspect_neotoma(target)['status']})
    except Exception as exc:
        probes.append({'case': 'external_manifest_symlink', 'exception': type(exc).__name__,
                       'code': getattr(exc, 'code', None)})
    receipt['manifest_probes'] = probes
    (root / 'transport-bundle-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


asyncio.run(main())
