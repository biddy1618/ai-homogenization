import csv, sys, collections
from statistics import mean
data, queries = sys.argv[1], sys.argv[2]

core=set(); per=collections.defaultdict(list)
for line in open(queries, encoding='utf-8'):
    line=line.strip()
    if not line or line.startswith('#') or '|' not in line: continue
    c,q=[x.strip() for x in line.split('|',1)]
    per[c].append(q)
for c,qs in per.items(): core.update(qs[:9])

rows=list(csv.DictReader(open(data, encoding='utf-8')))
runs=collections.defaultdict(list)
for r in rows: runs[r['date']].append(r)

print(f"{'date':12} {'n':>4} {'sim_all':>8} {'sim_45':>8} {'vendi':>7} {'vendi45':>8}")
for d in sorted(runs):
    rs=runs[d]
    c=[r for r in rs if r['query'] in core]
    f=lambda s,k: f"{mean(float(r[k]) for r in s):.4f}" if s else "  -   "
    print(f"{d:12} {len(rs):>4} {f(rs,'mean_pairwise_cosine'):>8} {f(c,'mean_pairwise_cosine'):>8} {f(rs,'vendi'):>7} {f(c,'vendi'):>8}")

last=sorted(runs)[-1]; rs=runs[last]
print(f"\n--- latest run {last} (n={len(rs)}) ---")
bydom=collections.defaultdict(list)
for r in rs: bydom[r['category']].append(float(r['mean_pairwise_cosine']))
for c,v in sorted(bydom.items(), key=lambda x:-mean(x[1])): print(f"  {c:10} {mean(v):.4f}  (n={len(v)})")
s=sorted(rs, key=lambda r: float(r['mean_pairwise_cosine']))
print("\n most alike:", [(r['query'], round(float(r['mean_pairwise_cosine']),3)) for r in s[-3:]][::-1])
print(" most varied:", [(r['query'], round(float(r['mean_pairwise_cosine']),3)) for r in s[:3]])
print(f"\n latest mean vendi: {mean(float(r['vendi']) for r in rs):.3f}")
print(f" share of questions with vendi < 2.0: {sum(1 for r in rs if float(r['vendi'])<2)/len(rs):.1%}")
print(f" share with similarity > 0.8: {sum(1 for r in rs if float(r['mean_pairwise_cosine'])>0.8)/len(rs):.1%}")
