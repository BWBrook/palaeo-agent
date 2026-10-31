"""Compare sealed independent answers with keys; the generator is never read."""
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[3]
predictions=OUT/'predictions.json'
seal=json.loads((OUT/'seal.json').read_text())
assert hashlib.sha256(predictions.read_bytes()).hexdigest()==seal['predictions_sha256']
record=json.loads(predictions.read_text())
assert all(hashlib.sha256((REPO/name).read_bytes()).hexdigest()==value for name,value in record['materials_sha256'].items())
comparisons=[]
for item in record['items']:
    keypath=REPO/'evaluation/pilot'/item['item']/'key.json'
    key=json.loads(keypath.read_text())
    fields=[]
    for field,expected in key['results'].items():
        actual=item['results'][field]
        delta=abs(actual-expected)
        tolerance=0 if field in key['integer_results'] else key['tolerance']['abs']+key['tolerance']['rel']*abs(expected)
        fields.append({'field':field,'independent':actual,'key':expected,'absolute_error':delta,'tolerance':tolerance,'matches':delta<=tolerance})
    signatures=[]
    for signature in key['failure_signatures']:
        margins={name:abs(value-key['results'][name])/(key['tolerance']['abs']+key['tolerance']['rel']*abs(key['results'][name])) for name,value in signature['results'].items()}
        signatures.append({'name':signature['name'],'conservative_tolerance_multiples':margins,'largest_margin':max(margins.values())})
    comparisons.append({'item':item['item'],'key_sha256':hashlib.sha256(keypath.read_bytes()).hexdigest(),'numeric_match':all(f['matches'] for f in fields),'fields':fields,'key_expected':key['expected'],'independent_status':item['status'],'key_sufficiency_witness':key['sufficiency_witness'],'key_exclusions_expected':key['exclusions_expected'],'independent_excluded_ids':item['excluded_ids'],'signature_separation':signatures})
report={'predictions_sha256':seal['predictions_sha256'],'generator_read':False,'all_16_numeric_match':all(c['numeric_match'] for c in comparisons),'maximum_absolute_error':max(f['absolute_error'] for c in comparisons for f in c['fields']),'field_count':sum(len(c['fields']) for c in comparisons),'comparisons':comparisons}
with (OUT/'comparison.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in report.items() if k!='comparisons'}))
