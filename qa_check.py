#!/usr/bin/env python3
"""
QA / integrity check for the Synthetic 13F Dataset.
Independently recomputes the quarter-over-quarter changes from filings.csv and
verifies they match changes_ground_truth.csv exactly — plus structural and
sanity checks. Exit code 0 = clean.  Run: python3 qa_check.py
"""
import csv, collections, statistics, os, sys

DATA = os.path.join(os.path.dirname(__file__), "data")
QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4"]

filings = list(csv.DictReader(open(os.path.join(DATA, "filings.csv"))))
changes = list(csv.DictReader(open(os.path.join(DATA, "changes_ground_truth.csv"))))

issues = []

# 1) CUSIP -> issuer consistency (same id must always name the same issuer)
cusip_issuer = {}
for r in filings:
    c, n = r["cusip"], r["nameOfIssuer"]
    if c in cusip_issuer and cusip_issuer[c] != n:
        issues.append(f"CUSIP {c} maps to 2 issuers: {cusip_issuer[c]} / {n}")
    cusip_issuer[c] = n

# 2) no duplicate (manager, quarter, cusip); valid fields
seen = set()
for r in filings:
    k = (r["manager"], r["quarter"], r["cusip"])
    if k in seen:
        issues.append(f"duplicate holding row {k}")
    seen.add(k)
    if int(r["value_usd_thousands"]) <= 0:
        issues.append(f"non-positive value {k}")
    if int(r["sshPrnamt"]) <= 0:
        issues.append(f"non-positive shares {k}")
    if len(r["cusip"]) != 9:
        issues.append(f"bad CUSIP length {r['cusip']}")
    if r["quarter"] not in QUARTERS:
        issues.append(f"bad quarter {r['quarter']}")
    if r["votingAuthoritySole"] != r["sshPrnamt"]:
        issues.append(f"voting != shares {k}")

# 3) each manager-quarter must be non-empty
H = collections.defaultdict(lambda: collections.defaultdict(dict))
for r in filings:
    H[r["manager"]][r["quarter"]][r["cusip"]] = int(r["value_usd_thousands"])
for mgr in H:
    for q in QUARTERS:
        if not H[mgr].get(q):
            issues.append(f"empty portfolio {mgr} {q}")

# 4) THE BIG ONE: recompute changes from filings, compare to ground truth
recomputed = {}
for mgr in H:
    for i in range(1, len(QUARTERS)):
        pq, q = QUARTERS[i - 1], QUARTERS[i]
        before, after = H[mgr].get(pq, {}), H[mgr].get(q, {})
        for c in set(before) | set(after):
            b, a = before.get(c, 0), after.get(c, 0)
            ch = ("EXIT" if b and not a else "NEW" if a and not b
                  else "HOLD" if a == b else "ADD" if a > b else "TRIM")
            recomputed[(mgr, q, c)] = (ch, b, a)

gt = {(r["manager"], r["to_quarter"], r["cusip"]):
      (r["change"], int(r["value_before_k"]), int(r["value_after_k"])) for r in changes}

mismatch = 0
for k in set(recomputed) | set(gt):
    if recomputed.get(k) != gt.get(k):
        mismatch += 1
        if mismatch <= 10:
            issues.append(f"CHANGE MISMATCH {k}: filings={recomputed.get(k)} vs gt={gt.get(k)}")

# 5) stats
per_mq = collections.Counter((r["manager"], r["quarter"]) for r in filings)
counts = list(per_mq.values())
vals = [int(r["value_usd_thousands"]) for r in filings]
print(f"filings rows                 : {len(filings)}")
print(f"change rows                  : {len(changes)}")
print(f"unique CUSIPs                : {len(cusip_issuer)}")
print(f"positions per manager-quarter: min {min(counts)}  max {max(counts)}  mean {statistics.mean(counts):.1f}")
print(f"value_usd_thousands          : min {min(vals)}  median {int(statistics.median(vals))}  max {max(vals)}")
print(f"change label counts          : {dict(collections.Counter(r['change'] for r in changes))}")
print(f"ground-truth vs recomputed mismatches: {mismatch}")
print(f"TOTAL ISSUES                 : {len(issues)}")
for x in issues[:20]:
    print("  -", x)

sys.exit(1 if issues else 0)
