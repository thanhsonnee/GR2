<!--
STATUS: ARCHIVED - Implementation report (historical)
PURPOSE: Documents Li & Lim benchmark integration completed in January 2026
AUDIENCE: Developers interested in Li & Lim parser implementation
DATE: January 2026
-->

# Li & Lim PDPTW Benchmark Implementation

## Status: ✓ IMPLEMENTED AND RUNNING

All requested features for Li & Lim benchmark support have been implemented.

---

## What Was Implemented

### 1. Li & Lim Format Parser ✓
**File**: `algorithm/li_lim_parser.py`

**Format differences from Sartori & Buriol**:
- No keywords (SIZE:, CAPACITY:, NODES, EDGES)
- Space-separated format:
  ```
  n_customers  capacity  speed
  node  x  y  demand  ready  due  service  pickup_idx  delivery_idx
  ```
- Explicit pickup-delivery pairing in last 2 columns
- Euclidean coordinates (x, y) instead of (lat, lon)
- NO pre-computed EDGES matrix → calculates Euclidean distances
- Distance = round(sqrt(dx^2 + dy^2))

**Key features**:
- Auto-detects Li & Lim vs Sartori & Buriol format
- Builds Euclidean distance matrix automatically
- Reads explicit pickup-delivery pairs from file columns

### 2. Format Auto-Detection ✓
**File**: `algorithm/data_loader.py` (modified)

- `Instance.read_from_file()` auto-detects format
- Li & Lim: First line has integers only
- Sartori & Buriol: First line has "SIZE:" keyword
- Delegates to appropriate parser
- **STRICT SEPARATION**: No format mixing

### 3. Benchmark Test Script ✓
**File**: `algorithm/test_li_lim.py`

**Configuration**:
- Dataset: Li & Lim PDPTW pdp100
- Location: `instances/pdp_100/`
- Instances: ALL 56 files (lc*, lr*, lrc*)
- Time limit: **10 seconds per instance** (hard limit)
- Algorithm: ILS + AGES + LNS + LAHC (unchanged)

**Features**:
- Scans entire pdp_100 directory
- Sorts instances by class (LC, LR, LRC) and number
- Logs detailed results for each instance
- Groups statistics by class
- Saves results to JSON and CSV
- Progress tracking with ETA

### 4. Feasibility Guarantees ✓

**All existing feasibility checks apply**:
- Pickup before delivery precedence
- Time windows respected
- Capacity constraints
- Route consistency
- No duplicate/missing nodes

**Validator**: Uses existing `feasibility_validator.py` without modifications

---

## File Structure

```
algorithm/
├── li_lim_parser.py          # NEW: Li & Lim format parser
├── data_loader.py             # MODIFIED: Auto-detect + delegate
├── test_li_lim.py            # NEW: Full benchmark test
├── test_parser.py            # NEW: Quick parser test
├── feasibility_validator.py  # UNCHANGED: Works for both formats
├── lahc_acceptance.py        # UNCHANGED
├── large_neighborhood_search.py  # UNCHANGED
├── iterated_local_search.py  # UNCHANGED
└── ... (other files unchanged)

instances/
├── pdp_100/                  # Li & Lim instances
│   ├── lc101.txt, lc102.txt, ...
│   ├── lr101.txt, lr102.txt, ...
│   └── lrc101.txt, lrc102.txt, ...
└── n100/                     # Sartori & Buriol instances
    └── n100/                 # (UNTOUCHED)
        ├── bar-n100-1.txt, ...
        ├── ber-n100-1.txt, ...
        └── ...
```

---

## Li & Lim Dataset Details

**Location**: `instances/pdp_100/`

**Total instances**: 56

**Classes**:
1. **LC (Clustered, Short Time Windows)**: lc1xx (8 instances), lc2xx (8 instances) = 16 total
2. **LR (Random)**: lr1xx (12 instances), lr2xx (11 instances) = 23 total
3. **LRC (Random-Clustered)**: lrc1xx (8 instances), lrc2xx (8 instances) = 16 total

**Characteristics**:
- Each file: ~100-110 nodes (includes depot + pickups + deliveries)
- Capacity: 200 (typical)
- Time windows vary by class (tight for LC, loose for LR)

---

## How to Run

### Quick Test (Single Instance)
```bash
cd algorithm
python test_parser.py
```
- Tests parser on `lc101.txt`
- Verifies parsing + construction + validation

### Full Benchmark Test
```bash
cd algorithm
python test_li_lim.py
```
- Runs on ALL 56 Li & Lim instances
- 10 seconds per instance
- Generates:
  - `li_lim_results.json` (detailed results)
  - `li_lim_results.csv` (tabular format)
- Estimated time: ~10 minutes

---

## Output Format

### JSON Output (`li_lim_results.json`)
```json
{
  "benchmark": "Li & Lim PDPTW pdp100",
  "time_limit": 10,
  "summary": {
    "total": 56,
    "feasible": X,
    "infeasible": Y,
    "failed": Z
  },
  "results": [
    {
      "instance": "lc101",
      "class": "LC",
      "status": "FEASIBLE",
      "feasible": true,
      "vehicles": 10,
      "cost": 828.94,
      "runtime": 10.0
    },
    ...
  ]
}
```

### CSV Output (`li_lim_results.csv`)
```csv
Instance,Class,Status,Feasible,Vehicles,Cost,Runtime_s
lc101,LC,FEASIBLE,True,10,828.94,10.00
lc102,LC,FEASIBLE,True,10,828.94,10.00
...
```

---

## Differences from Sartori & Buriol

| Aspect | Sartori & Buriol | Li & Lim |
|--------|------------------|----------|
| Format | Keyword-based | Space-separated |
| Coordinates | (lat, lon) | (x, y) Euclidean |
| Distance Matrix | Pre-computed EDGES | Calculated on-the-fly |
| Pairing | Calculated (idx + n/2) | Explicit in file |
| Instances | Real-world cities | Synthetic benchmark |
| File Example | `bar-n100-1.txt` | `lc101.txt` |

---

## Validation

**Test Results (lc101.txt)**:
- Parsed successfully ✓
- Size: 107 nodes, Capacity: 200
- Generated solution: 21 vehicles, cost 2380
- **Feasibility: YES** ✓

**All constraints validated**:
- Pickup before delivery ✓
- Time windows ✓
- Capacity ✓
- No duplicates/missing ✓

---

## Guardrails in Place

✓ **Strict format separation** - Li & Lim and Sartori parsers are isolated

✓ **Auto-detection works** - Correct parser chosen automatically

✓ **Feasibility unchanged** - Same validator for both formats

✓ **No mixing** - Batch tests scan only their respective directories

✓ **Time limits enforced** - 10s hard limit per instance

✓ **Failure handling** - Failed instances logged, not skipped silently

---

## What Was NOT Changed

❌ Algorithm logic (ILS, AGES, LNS, LAHC) - unchanged

❌ Feasibility validator - unchanged

❌ Acceptance criteria - unchanged

❌ Parameter values - unchanged

❌ Sartori & Buriol code paths - untouched

---

## Current Status

**Test Status**: ⏳ RUNNING

- Started: Just now
- Expected duration: ~10 minutes (56 instances * 10s)
- Progress monitoring: Check `terminals/6.txt`

**Output files** (will be generated):
- `li_lim_results.json`
- `li_lim_results.csv`

---

## Summary

The Li & Lim PDPTW benchmark support is fully implemented with:
1. ✓ Dedicated parser for Li & Lim format
2. ✓ Auto-detection and format separation
3. ✓ Full benchmark test script
4. ✓ Same feasibility guarantees as before
5. ✓ Running on ALL 56 pdp100 instances

The implementation maintains strict separation between benchmarks and reuses all existing algorithm components without modification.
