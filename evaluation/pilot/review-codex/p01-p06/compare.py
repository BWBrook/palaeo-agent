"""Post-seal comparison against keyed values; never reads the generator."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BANK=HERE.parents[1]
pred_path=HERE/'predictions.json'
seal=json.loads((HERE/'seal.json').read_text())
assert hashlib.sha256(pred_path.read_bytes()).hexdigest()==seal['prediction_sha256']
assert hashlib.sha256((HERE/'recompute.py').read_bytes()).hexdigest()==seal['script_sha256']
sealed=json.loads(pred_path.read_text())
comparisons=[]
key_hashes={}
for identifier,pred in sealed['predictions'].items():
    keypath=BANK/identifier/'key.json'
    key=json.loads(keypath.read_text())
    key_hashes[str(keypath.relative_to(BANK))]=hashlib.sha256(keypath.read_bytes()).hexdigest()
    candidate=pred['results'] or pred['conditional_results']
    stats={}
    for name,expected in key['results'].items():
        actual=candidate[name]
        tol=key['tolerance']['abs']+key['tolerance']['rel']*abs(expected)
        stats[name]={'independent':actual,'key':expected,'difference':actual-expected,'within_tolerance':abs(actual-expected)<=tol}
    known={
        'zeros_as_sample':pred.get('nonidentifiability_witness',{}).get('zero_actual_counts'),
        'join_by_position':pred.get('incorrect_positional_results'),
        'percentages_as_counts':pred.get('incorrect_percentage_results'),
        'different_taxon_basis':pred.get('nonidentifiability_witness',{}).get('unobserved_each_equals_0'),
        'variants_as_species':pred.get('incorrect_unmerged_results'),
        'aliquots_as_units':pred.get('incorrect_aliquot_results'),
    }
    signatures=[]
    for signature in key['failure_signatures']:
        actual=known[signature['name']]
        assert actual is not None
        signatures.append({'name':signature['name'],'statistics':{
            name:{'independent':actual[name],'key':expected,'difference':actual[name]-expected,
                  'within_tolerance':abs(actual[name]-expected)<=key['tolerance']['abs']+key['tolerance']['rel']*abs(expected)}
            for name,expected in signature['results'].items()}})
    comparisons.append({'item':identifier,'numeric_comparison_uses':'primary' if pred['results'] else 'conditional changed-target calculation',
        'all_numbers_agree':all(r['within_tolerance'] for r in stats.values()),'statistics':stats,
        'status_conflict':pred['status']=='stopped' and key['expected']=='complete',
        'independent_handling':pred['handling'],'independent_sufficiency':pred['sufficiency'],
        'key_witness':key['sufficiency_witness'],'failure_signatures':signatures})
output={'sealed_predictions_sha256':seal['prediction_sha256'],'key_sha256':key_hashes,'comparisons':comparisons,
        'summary':{'items':len(comparisons),'numeric_agreements':sum(c['all_numbers_agree'] for c in comparisons),
        'unconditional_status_conflicts':[c['item'] for c in comparisons if c['status_conflict']],
        'incorrect_failure_signatures':[{'item':c['item'],'signature':s['name']} for c in comparisons for s in c['failure_signatures'] if not all(v['within_tolerance'] for v in s['statistics'].values())]}}
with (HERE/'comparison.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
print(json.dumps(output['summary']))
