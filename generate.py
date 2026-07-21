#!/usr/bin/env python3
"""
Green AI Labs — Synthetic 13F Dataset Generator
================================================
Generates a fully synthetic dataset of institutional-style quarterly holdings
("13F-like" information tables) for a roster of MADE-UP managers across four
quarters. Nothing here is real: every manager, issuer, CUSIP, and position is
randomly generated and belongs to nobody.

Why it exists: so you can build and test a "what changed across quarters"
analyzer without touching real filings or fighting data access. Because the
generator owns the ground truth, it also emits a changes file you can grade
your analyzer against.

Stdlib only. Seeded for reproducibility. Run:  python3 generate.py
"""

import csv
import os
import random
import string

SEED = 20260721
random.seed(SEED)

OUT = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT, exist_ok=True)

QUARTERS = ["2025Q1", "2025Q2", "2025Q3", "2025Q4"]

# --- Made-up managers -------------------------------------------------------
MANAGERS = [
    "Meridian Peak Capital Management",
    "Northwind Asset Advisors",
    "Cobalt Harbor Partners",
    "Vantage Ridge Capital",
    "Solstice Lane Investments",
    "Ironwood Meridian Advisors",
    "Blue Delta Capital Group",
    "Kestrel Point Management",
]

# --- Synthetic security universe -------------------------------------------
ISSUER_PREFIX = ["Cobalt", "Vantage", "Northwind", "Aster", "Quill", "Bright",
                 "Granite", "Lumen", "Cedar", "Onyx", "Vertex", "Halcyon",
                 "Pinnacle", "Sable", "Marlin", "Zephyr", "Copper", "Solace",
                 "Fable", "Drift", "Nova", "Terra", "Cirrus", "Basalt"]
ISSUER_CORE = ["Dynamics", "Robotics", "Systems", "Bioworks", "Logistics",
               "Semiconductor", "Therapeutics", "Networks", "Materials",
               "Analytics", "Energy", "Software", "Holdings", "Industries",
               "Micro", "Capital", "Foods", "Health", "Motors", "Cloud"]
ISSUER_SUFFIX = ["Inc", "Corp", "Group", "Co", "PLC", "Ltd"]

def make_cusip():
    # Synthetic 9-char CUSIP-like identifier (not a valid real CUSIP).
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(9))

def build_universe(n=220):
    seen_names, seen_cusips, universe = set(), set(), []
    while len(universe) < n:
        name = f"{random.choice(ISSUER_PREFIX)} {random.choice(ISSUER_CORE)} {random.choice(ISSUER_SUFFIX)}"
        cusip = make_cusip()
        if name in seen_names or cusip in seen_cusips:
            continue
        seen_names.add(name); seen_cusips.add(cusip)
        universe.append({
            "nameOfIssuer": name,
            "titleOfClass": random.choice(["COM", "COM", "COM", "CL A", "ADR"]),
            "cusip": cusip,
            "price": round(random.uniform(5, 480), 2),  # synthetic price to derive shares
        })
    return universe

UNIVERSE = build_universe()

def new_position(sec):
    # value reported in $thousands, like real 13Fs
    value_k = int(round(random.lognormvariate(9.5, 1.15)))  # ~ tens of thousands of $000s
    value_k = max(value_k, 100)
    shares = int(round(value_k * 1000 / sec["price"]))
    return {"value_k": value_k, "shares": max(shares, 1)}

def adjust_position(pos, sec):
    # quarter-over-quarter drift; occasional big add / big trim
    roll = random.random()
    if roll < 0.12:
        factor = random.uniform(1.5, 3.0)      # big add
    elif roll < 0.24:
        factor = random.uniform(0.2, 0.6)      # big trim
    else:
        factor = random.uniform(0.85, 1.18)    # normal drift
    new_val = max(int(round(pos["value_k"] * factor)), 50)
    shares = int(round(new_val * 1000 / sec["price"]))
    return {"value_k": new_val, "shares": max(shares, 1)}

sec_by_cusip = {s["cusip"]: s for s in UNIVERSE}

filings_rows = []
changes_rows = []

for mgr in MANAGERS:
    # initial portfolio
    size = random.randint(28, 60)
    holdings = {}  # cusip -> position
    for sec in random.sample(UNIVERSE, size):
        holdings[sec["cusip"]] = new_position(sec)

    prev_holdings = None
    for q in QUARTERS:
        if prev_holdings is not None:
            # exits
            n_exit = max(1, int(len(holdings) * random.uniform(0.08, 0.18)))
            for cusip in random.sample(list(holdings), min(n_exit, len(holdings))):
                del holdings[cusip]
            # new buys
            n_new = max(1, int(len(holdings) * random.uniform(0.08, 0.18)))
            candidates = [s for s in UNIVERSE if s["cusip"] not in holdings]
            for sec in random.sample(candidates, min(n_new, len(candidates))):
                holdings[sec["cusip"]] = new_position(sec)
            # adjust the rest
            for cusip, pos in list(holdings.items()):
                if cusip in prev_holdings:
                    holdings[cusip] = adjust_position(pos, sec_by_cusip[cusip])

        # emit filing rows for this quarter
        for cusip, pos in holdings.items():
            sec = sec_by_cusip[cusip]
            filings_rows.append({
                "manager": mgr,
                "quarter": q,
                "nameOfIssuer": sec["nameOfIssuer"],
                "titleOfClass": sec["titleOfClass"],
                "cusip": cusip,
                "value_usd_thousands": pos["value_k"],
                "sshPrnamt": pos["shares"],
                "sshPrnamtType": "SH",
                "investmentDiscretion": "SOLE",
                "votingAuthoritySole": pos["shares"],
            })

        # ground-truth changes vs previous quarter
        if prev_holdings is not None:
            all_cusips = set(prev_holdings) | set(holdings)
            for cusip in all_cusips:
                sec = sec_by_cusip[cusip]
                before = prev_holdings.get(cusip)
                after = holdings.get(cusip)
                if before and not after:
                    change = "EXIT"
                elif after and not before:
                    change = "NEW"
                else:
                    d = after["value_k"] - before["value_k"]
                    if d == 0:
                        change = "HOLD"
                    elif d > 0:
                        change = "ADD"
                    else:
                        change = "TRIM"
                changes_rows.append({
                    "manager": mgr,
                    "from_quarter": QUARTERS[QUARTERS.index(q) - 1],
                    "to_quarter": q,
                    "nameOfIssuer": sec["nameOfIssuer"],
                    "cusip": cusip,
                    "change": change,
                    "value_before_k": before["value_k"] if before else 0,
                    "value_after_k": after["value_k"] if after else 0,
                })

        prev_holdings = dict(holdings)

# --- write CSVs -------------------------------------------------------------
with open(os.path.join(OUT, "filings.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(filings_rows[0].keys()))
    w.writeheader(); w.writerows(filings_rows)

with open(os.path.join(OUT, "changes_ground_truth.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(changes_rows[0].keys()))
    w.writeheader(); w.writerows(changes_rows)

with open(os.path.join(OUT, "managers.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["manager", "quarters_filed"])
    for m in MANAGERS:
        w.writerow([m, "|".join(QUARTERS)])

print(f"managers: {len(MANAGERS)}  quarters: {len(QUARTERS)}")
print(f"filing rows: {len(filings_rows)}")
print(f"change rows: {len(changes_rows)}")
print(f"universe size: {len(UNIVERSE)}")
