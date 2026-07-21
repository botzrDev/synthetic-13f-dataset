# The Synthetic 13F Dataset

**A fully synthetic, ready-to-build dataset of institutional-style quarterly holdings — from Green AI Labs.**

Everything in here is made up. Every manager, issuer, CUSIP, and position was randomly generated and belongs to nobody. There are no real holdings, no real companies, and no real filings anywhere in this dataset. Any resemblance to a real security or fund is coincidental.

## Why this exists

If you want to build an AI tool that reads institutional filings and summarizes *what changed* quarter over quarter, real 13F data is a minefield — access limits, messy formatting, and the deeper problem of reasoning over real people's real money just to test your parser. This dataset lets you skip all of that and start building.

The bonus: because a generator produced this data, it also **owns the ground truth**. A `changes_ground_truth.csv` is included so you can grade your analyzer's "what changed" output against the real answer — something you never get with real filings.

## What's inside

| File | What it is |
|---|---|
| `data/filings.csv` | 1,537 holdings rows — 8 managers × 4 quarters (2025Q1–Q4), 13F-style columns |
| `data/changes_ground_truth.csv` | The true quarter-over-quarter change for every position: NEW, EXIT, ADD, TRIM, HOLD |
| `data/managers.csv` | The roster of (fictional) managers and the quarters they filed |
| `generate.py` | The generator itself, seeded — reproduce or extend the dataset yourself |
| `qa_check.py` | Integrity check — independently recomputes the changes from the filings and confirms they match the answer key (verified: 0 mismatches) |

### `filings.csv` columns
`manager`, `quarter`, `nameOfIssuer`, `titleOfClass`, `cusip`, `value_usd_thousands`, `sshPrnamt` (shares), `sshPrnamtType`, `investmentDiscretion`, `votingAuthoritySole` — modeled on the real 13F information-table schema (values in $thousands, like the real thing).

### `changes_ground_truth.csv` columns
`manager`, `from_quarter`, `to_quarter`, `nameOfIssuer`, `cusip`, `change`, `value_before_k`, `value_after_k`.

**Change labels:** `NEW` (position opened this quarter), `EXIT` (position closed), `ADD` (value increased), `TRIM` (value decreased), `HOLD` (value *exactly* unchanged — rare by design, since most retained positions move at least a little, so they land in ADD/TRIM).

## How to use it

1. Point your parser at `filings.csv` and build a clean, per-manager, per-quarter view.
2. Compute the diff between consecutive quarters (new / exit / add / trim).
3. Grade your output against `changes_ground_truth.csv` — that's your accuracy check.
4. Add an AI layer to *explain* the diff in plain English — but let deterministic code decide *what's in the filing* (the hard-won lesson from the teardown that shipped with this).

**Verify the answer key yourself:** run `python3 qa_check.py`. It recomputes every quarter-over-quarter change directly from `filings.csv` and confirms it matches `changes_ground_truth.csv` (plus structural sanity checks). It should report 0 mismatches and 0 issues.

## Reproduce or extend it

```
python3 generate.py
```

It's seeded (`SEED = 20260721`), so you get the same dataset every run. Change the seed, the manager roster, the universe size, or the turnover rates to generate your own variations.

## License

Public domain / CC0 — use it for anything, no attribution required. It's fake data; go build.

## A note on what this is (and isn't)

This is **engineering education material**. It is synthetic data for learning how to build software. It is **not** investment advice, not a dataset of real holdings, and not a signal about any real security. Nothing here is a recommendation to buy, sell, or hold anything.

---

Built by **Green AI Labs** — finance AI, built on synthetic data. More teardowns and datasets: https://greenailabs.beehiiv.com
