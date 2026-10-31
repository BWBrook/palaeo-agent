import csv, json, itertools
rows = list(csv.reader(open('assemblages.tsv'), delimiter='\t'))
S = {r[0]: [float(x) for x in r[1:]] for r in rows[1:]}
C = {}
for s, v in S.items():
    c = [n for n in range(1, 3001)
         if all(abs(round(x * n / 100) * 100 / n - x) <= 0.005 + 1e-9 for x in v)
         and sum(round(x * n / 100) for x in v) == n]
    print(s, c[:5])
    C[s] = [round(x * c[0] / 100) for x in v] if c else None
names = list(S)
res = {}
for a, b in itertools.combinations(names, 2):
    x, y = C[a], C[b]
    res[f"{a}|{b}"] = 1 - 2 * sum(min(i, j) for i, j in zip(x, y)) / (sum(x) + sum(y))
print(C)
print(res)
json.dump(res, open('bc_res.json', 'w'))
