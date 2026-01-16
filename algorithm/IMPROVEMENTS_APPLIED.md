# IMPROVEMENTS APPLIED - Quality Enhancement

**Date**: January 11, 2026  
**Goal**: Reduce gap to BKS from +100% to <+30%

---

## CHANGES IMPLEMENTED

### ✅ FIX 1: BKS Database (bks_li_lim.py)

**Created**: `algorithm/bks_li_lim.py`

**Content**:
- 56 Li & Lim instances BKS values
- Source: SINTEF TOP + Li & Lim (2003) paper
- Functions: `get_bks()`, `calculate_gap()`

**Impact**: Can now measure real gaps to best known solutions

---

### ✅ FIX 2: Time Limit Increased (test_li_lim.py)

**Changed**: `TIME_LIMIT_PER_INSTANCE = 10` → `60`

**Reason**: 
- 10s too short for quality solutions
- 60s allows more LNS iterations
- Trade-off: Total runtime 10min → 60min for 56 instances

**Impact**: ~20-30% quality improvement expected

---

### ✅ FIX 3: LNS Destroy Size Increased (large_neighborhood_search.py)

**Changed**:
- `min_destroy_size = 3` → `5`
- `max_destroy_size = 15` → `25`

**Reason**:
- Destroy 3-15 pairs too conservative
- Destroy 5-25 pairs = more exploration
- More aggressive destroy → escape local optima better

**Impact**: ~10-15% quality improvement expected

---

### ✅ BONUS: BKS Integration in Results

**Modified**: `test_li_lim.py`

**Added to output**:
```python
# Console output
print(f"  BKS: {bks_vehicles} veh, {bks_cost:.2f} cost")
print(f"  GAP: {gap_vehicles:+.1f}% (veh), {gap_cost:+.1f}% (cost)")

# CSV columns
Instance,Class,Status,Feasible,Vehicles,Cost,Runtime_s,BKS_Veh,BKS_Cost,Gap_Veh_%,Gap_Cost_%
```

**Impact**: Clear visibility of performance vs BKS

---

### ✅ BONUS: ILS Iterations Reduced

**Changed**: `max_iterations = 100` → `20`

**Reason**: Focus computational budget on LNS quality instead of many quick ILS iterations

---

## EXPECTED RESULTS

### Before (10s, destroy 3-15)
| Instance | Result | BKS | Gap |
|----------|--------|-----|-----|
| lc101 | 20 veh, 2336 | 10 veh, 828.94 | +100% veh, +181% cost |
| lc201 | 6 veh, 2370 | 3 veh, 591.56 | +100% veh, +301% cost |
| lr101 | 29 veh, 2512 | 19 veh, 1650.80 | +53% veh, +52% cost |

### After (60s, destroy 5-25, BKS tracking)
| Instance | Expected | BKS | Expected Gap |
|----------|----------|-----|--------------|
| lc101 | **12-14 veh, ~1000-1200** | 10 veh, 828.94 | +20-40% veh, +20-40% cost |
| lc201 | **4-5 veh, ~700-800** | 3 veh, 591.56 | +33-67% veh, +18-35% cost |
| lr101 | **21-23 veh, ~1800-1900** | 19 veh, 1650.80 | +11-21% veh, +9-15% cost |

**Overall expected**: 
- Average vehicle gap: +20-35% (down from +50-100%)
- Average cost gap: +15-30% (down from +50-180%)
- Still not matching BKS, but competitive for a heuristic

---

## WHY NOT PERFECT?

**BKS are from highly tuned algorithms:**
- Ropke & Pisinger (2006): ALNS with adaptive weights + SA acceptance
- Curtois et al. (2018): Heavy parameter tuning + domain-specific operators
- Sartori & Buriol (2020): Matheuristic with MILP-based Set Partitioning

**Our approach is simpler:**
- Fixed operators (no adaptive weights yet)
- LAHC acceptance (simpler than SA)
- Greedy Set Partitioning (not MILP-based)
- Greedy construction (not Solomon I1 yet)

**To match BKS would require:**
1. Solomon I1 construction heuristic (planned)
2. 2-opt* and relocate operators (planned)
3. Adaptive operator selection (complex)
4. Much longer runtime (hours vs minutes)

---

## NEXT STEPS (IF STILL NOT GOOD ENOUGH)

### Priority 1: Solomon I1 Construction
**Effort**: 2-3 hours  
**Expected impact**: -20-30% vehicles

### Priority 2: Inter-route Operators (2-opt*, relocate)
**Effort**: 2-3 hours  
**Expected impact**: -10-15% cost

### Priority 3: Adaptive Weights (like ALNS)
**Effort**: 4-6 hours  
**Expected impact**: -5-10% overall

---

## HOW TO RUN

```bash
cd algorithm

# Full test (60s per instance, ~60 minutes total)
python test_li_lim.py

# Check results
python check_feasible.py
python check_csv.py

# View gaps
# Open li_lim_results.csv in Excel
# Sort by Gap_Cost_% column to see worst instances
```

---

## FILES MODIFIED

1. **algorithm/bks_li_lim.py** (NEW) - BKS database
2. **algorithm/test_li_lim.py** - Time limit + BKS integration
3. **algorithm/large_neighborhood_search.py** - Destroy size
4. **algorithm/IMPROVEMENTS_APPLIED.md** (this file)

---

**Status**: ✅ READY TO TEST  
**Next action**: Run `python test_li_lim.py` and compare with previous results
