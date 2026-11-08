import csv, sys, collections, json
rows=[r for r in csv.DictReader(open(sys.argv[1], encoding='utf-8')) if r['date']=='2026-11-02']
order=['finance','health','law','science','tech']
out=[]
for c in order:
    vs=sorted((float(r['mean_pairwise_cosine']) for r in rows if r['category']==c), reverse=True)
    out.append([c, [round(v,3) for v in vs]])
print(json.dumps(out))
print("total", sum(len(v) for _,v in out))
