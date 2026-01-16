# FINAL IMPROVEMENTS - Targeting Better BKS Gaps

**Date**: January 11, 2026  
**Goal**: Reduce lc101 from 21 veh → closer to BKS 10 veh

---

## PROBLEM IDENTIFIED

User feedback from test results:
- ✅ lc104: 14 vehicles (BKS: 9) → Gap +55% (acceptable)
- ❌ lc101: 21 vehicles (BKS: 10) → Gap +110% (too high!)

**Analysis**: lc101 is "easier" than lc104 but results are worse → algorithm needs more aggressive exploration

---

## IMPROVEMENTS APPLIED

### 1. Time Limit: 20s → 30s

**File**: `test_li_lim.py`  
**Change**: `TIME_LIMIT_PER_INSTANCE = 20` → `30`

**Reason**: 
- 20s not enough for quality convergence
- 30s allows 2-3 more ILS iterations
- Still reasonable for practical use

**Impact**: 
- Total time: 20 min → ~25-28 min
- Expected quality: +10-15% improvement

---

### 2. LNS Destroy Size: 5-25 → 8-30 pairs

**File**: `large_neighborhood_search.py`  
**Change**: 
- `min_destroy_size = 5` → `8`
- `max_destroy_size = 25` → `30`

**Reason**:
- 5-25 still too conservative
- 8-30 = destroy up to 60% of solution
- More aggressive = escape local optima better

**Impact**: Expected -15-20% vehicles for stuck solutions

---

### 3. LNS Iterations: 200 → 500

**File**: `iterated_local_search.py`  
**Change**: `max_iterations = 200` → `500`

**Reason**: More LNS iterations = more destroy-repair attempts = better solutions

**Impact**: Better cost optimization within same time

---

### 4. LNS Time: 15s → 20s per run

**File**: `iterated_local_search.py`  
**Change**: `max_time = 15` → `20`

**Reason**: Allow LNS to converge better before moving to next ILS iteration

**Impact**: Higher quality per iteration

---

## EXPECTED RESULTS

### Before (20s, destroy 5-25)
| Instance | Result | BKS | Gap |
|----------|--------|-----|-----|
| lc101 | 21 veh, 2262 | 10 veh, 828.94 | **+110% veh, +173% cost** ❌ |
| lc104 | 14 veh, 1410 | 9 veh, 860.01 | +55% veh, +64% cost |
| lr101 | 29 veh, 2512 | 19 veh, 1650.80 | +53% veh, +52% cost |

### After (30s, destroy 8-30, 500 iterations)
| Instance | Expected | BKS | Expected Gap |
|----------|----------|-----|--------------|
| lc101 | **13-15 veh, ~1100-1300** | 10 veh, 828.94 | **+30-50% veh, +33-57% cost** ✅ |
| lc104 | **11-12 veh, ~1000-1100** | 9 veh, 860.01 | +22-33% veh, +16-28% cost ✅ |
| lr101 | **22-24 veh, ~1900-2000** | 19 veh, 1650.80 | +16-26% veh, +15-21% cost ✅ |

**Overall target**: Average gap **+25-40%** (competitive heuristic range)

---

## PARAMETER SUMMARY

| Parameter | Old Value | New Value | Change |
|-----------|-----------|-----------|--------|
| Time limit | 10s | **30s** | +200% |
| Min destroy | 3 pairs | **8 pairs** | +167% |
| Max destroy | 15 pairs | **30 pairs** | +100% |
| LNS iterations | 100 | **500** | +400% |
| LNS time/run | 30s | **20s** | -33% (trade-off) |
| ILS iterations | 100 | **20** | -80% (focus on quality) |
| Early stopping | No | **Yes (5 iter)** | New |

**Philosophy**: Quality over quantity - fewer ILS iterations but higher quality each

---

## RUNTIME ESTIMATE

**With early stopping**:
- Easy instances: 15-20s (stop early)
- Medium instances: 25-30s (use full time)
- Hard instances: 30s (hit limit)

**Average**: ~25s per instance  
**Total**: 25s × 56 = **~23-25 minutes**

**Without early stopping**: 30s × 56 = **28 minutes**

---

## QUALITY vs SPEED COMPARISON

| Configuration | Time/Inst | Total (56) | lc101 Expected | Gap Quality |
|---------------|-----------|------------|----------------|-------------|
| **Original** | 10s | 10 min | 20 veh | +100% ⭐ |
| **Fast v1** | 20s | 20 min | 16-18 veh | +60-80% ⭐⭐ |
| **Current** | 30s | 25 min | 13-15 veh | **+30-50%** ⭐⭐⭐ |
| Ideal | 60s | 60 min | 11-13 veh | +10-30% ⭐⭐⭐⭐ |
| BKS | hours | N/A | 10 veh | 0% ⭐⭐⭐⭐⭐ |

**Current config** balances quality and speed for practical use.

---

## TEST STATUS

**Command**: `python test_li_lim.py`  
**Started**: Running now...  
**Expected completion**: ~25 minutes  
**Output files**:
- `li_lim_results.json` - Full results with BKS comparison
- `li_lim_results.csv` - Excel-friendly table

---

## HOW TO MONITOR PROGRESS

Check terminal output for real-time updates:
```bash
# View progress
cat c:\Users\HP\.cursor\projects\c-Users-HP-pdptw-instances\terminals\3.txt

# Or in PowerShell
Get-Content c:\Users\HP\.cursor\projects\c-Users-HP-pdptw-instances\terminals\3.txt -Tail 50
```

Look for:
- `[X/56]` - Current instance number
- `ETA: X min` - Estimated time remaining
- `[OK] FEASIBLE: X veh, cost Y` - Result per instance

---

## AFTER COMPLETION

Run analysis:
```bash
cd algorithm

# Check feasibility
python check_feasible.py

# View summary
python check_csv.py

# Open Excel
start li_lim_results.csv
```

---

## IF QUALITY STILL NOT GOOD ENOUGH

Next steps (in priority order):

### 1. Implement Solomon I1 Construction
- **Impact**: -20-30% vehicles
- **Effort**: 2-3 hours
- **Why**: Current greedy construction is too naive

### 2. Add 2-opt* Inter-route Operator
- **Impact**: -10-15% cost
- **Effort**: 2-3 hours
- **Why**: LNS alone doesn't optimize route structure

### 3. Adaptive Operator Selection (ALNS style)
- **Impact**: -5-10% overall
- **Effort**: 4-6 hours
- **Why**: Learn which operators work best

### 4. Increase Time to 60s
- **Impact**: -5-10% gap
- **Effort**: 1 minute (just change parameter)
- **Trade-off**: 60 min total runtime

---

## FILES MODIFIED

1. **test_li_lim.py** - Time limit 20→30s
2. **large_neighborhood_search.py** - Destroy 5-25→8-30 pairs
3. **iterated_local_search.py** - LNS iterations 200→500, time 15→20s
4. **FINAL_IMPROVEMENTS.md** (this file)

---

**Status**: 🏃 RUNNING (started now)  
**ETA**: ~25 minutes  
**Next**: Wait for completion, then analyze results
