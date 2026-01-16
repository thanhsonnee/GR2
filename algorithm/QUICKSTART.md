<!--
Purpose: Practical running guide for PDPTW solver
Audience: Users who want to run experiments
Status: ACTIVE
-->

# QUICKSTART - How to Run PDPTW Solver

**Prerequisites**: Python 3.7+, pip

---

## Setup (First Time Only)

### Step 1: Clone Repository
```bash
git clone https://github.com/cssartori/pdptw-instances.git
cd pdptw-instances
```
### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**Why?** Isolates dependencies, prevents conflicts with other Python projects.

### Step 3: Install Dependencies
```bash
cd algorithm
pip install -r requirements.txt
```

**Required packages**: See `requirements.txt` (currently: `numpy`)

**Verification**:
```bash
python -c "import numpy; print('Setup OK!')"
```

---

## Running Tests

### Option 1: Quick Test (3 Li & Lim instances, ~1 minute)
```bash
python test_li_lim_quick.py
```

**Tests**: lc101, lr101, lrc101  
**Time limit**: 10 seconds per instance  
**Output**: Console only

**Example output**:
```
[1/3] Testing lc101...
  Result: 20 veh, cost 2234, feasible=True ✓
```

---

### Option 2: Fast Test (10 representative instances, ~3-5 minutes) ⚡ RECOMMENDED
```bash
python test_li_lim_fast.py
```

**Tests**: 10 representative instances (2 from each class)  
**Time limit**: 20 seconds per instance  
**Total time**: ~3-5 minutes  
**Output**: `fast_test_results.json`

**Why use this?** Quick evaluation without waiting 20 minutes!

---

### Option 3: Full Li & Lim Benchmark (56 instances, ~15-20 minutes)
```bash
python test_li_lim.py
```

**Tests**: All pdp_100 instances (lc*, lr*, lrc*)  
**Time limit**: 20 seconds per instance  
**Early stopping**: Stops if no improvement for 5 iterations  
**Output**:
- `li_lim_results.json` - Detailed results
- `li_lim_results.csv` - Excel-friendly format with BKS comparison

---

### Option 3: Sartori & Buriol Test (3 instances, ~3 minutes)
```bash
python test_feasibility.py
```

**Tests**: bar-n100-1, bar-n100-2, bar-n100-3  
**Time limit**: 60 seconds per instance  
**Output**: `feasibility_test_results.json`

---

## Checking Results

### Check Feasibility (Most Important!)
```bash
python check_feasible.py
```

**Expected output**:
```
LI & LIM RESULTS
Total instances: 56
Feasible: 56/56 (100.0%)
ALL FEASIBLE - PERFECT!
```

**If you see `Infeasible`**: This is a bug - all solutions should be feasible.

---

### Check CSV Results
```bash
python check_csv.py
```

**Shows**: Statistics by class (LC, LR, LRC) and feasibility status.

---

## Running Custom Instances

### Method 1: Create a Python Script (Recommended)

**Step 1**: Create a new file `my_test.py` in the `algorithm/` directory:

```python
# my_test.py
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch

# Load instance (change path to your instance)
instance = Instance()
instance.read_from_file("../instances/pdp_100/lc101.txt")

print(f"Instance: {instance.name}")
print(f"Nodes: {instance.size}, Capacity: {instance.capacity}")

# Run ILS with custom parameters
ils = IteratedLocalSearch(
    instance, 
    max_iterations=100,  # More iterations = better quality (but slower)
    max_time=10          # Time limit in seconds
)

results = ils.solve()

# Check results
if results:
    print(f"\nResults:")
    print(f"  Vehicles: {results['vehicles']}")
    print(f"  Cost: {results['cost']}")
    print(f"  Feasible: {results['is_feasible']}")
    print(f"  Runtime: {results['runtime']:.2f}s")
    
    # Compare with best known
    if results.get('best_vehicles'):
        print(f"\nBest Known:")
        print(f"  Vehicles: {results['best_vehicles']}")
        print(f"  Cost: {results['best_cost']}")
        print(f"  Gap: {results['gap_vehicles']:.2f}% (vehicles), {results['gap_cost']:.2f}% (cost)")
else:
    print("Failed to find feasible solution!")
```

**Step 2**: Run the script:
```bash
cd algorithm
python my_test.py
```

---

### Method 2: Interactive Python (Quick Testing)

```bash
cd algorithm
python
```

Then in Python REPL:
```python
>>> from data_loader import Instance
>>> from iterated_local_search import IteratedLocalSearch

>>> # Load any instance
>>> instance = Instance()
>>> instance.read_from_file("../instances/pdp_100/lc101.txt")
>>> print(f"Loaded: {instance.name}")

>>> # Quick run
>>> ils = IteratedLocalSearch(instance, max_iterations=10, max_time=5)
>>> results = ils.solve()

>>> # Check feasibility
>>> print(f"Feasible: {results['is_feasible']}")
```

---

### Method 3: Test Multiple Custom Instances

Create `batch_custom.py`:
```python
from data_loader import Instance
from iterated_local_search import IteratedLocalSearch

# List your instances here
my_instances = [
    "../instances/pdp_100/lc101.txt",
    "../instances/pdp_100/lc102.txt",
    "../instances/n100/n100/bar-n100-1.txt"
]

for inst_path in my_instances:
    print(f"\n{'='*60}")
    print(f"Testing: {inst_path}")
    print('='*60)
    
    try:
        instance = Instance()
        instance.read_from_file(inst_path)
        
        ils = IteratedLocalSearch(instance, max_iterations=50, max_time=30)
        results = ils.solve()
        
        if results:
            print(f"Result: {results['vehicles']} veh, cost {results['cost']}, feasible={results['is_feasible']}")
        else:
            print("FAILED")
    except Exception as e:
        print(f"ERROR: {e}")
```

Run it:
```bash
python batch_custom.py
```

---

### Adjusting Algorithm Parameters

| Parameter | Default | Effect | Recommendation |
|-----------|---------|--------|----------------|
| `max_iterations` | 10 | More = better quality | 50-100 for experiments, 10 for quick tests |
| `max_time` | 300 | Time limit (seconds) | 10-30 for quick, 60-300 for quality |

**Example**: For high-quality solution on a hard instance:
```python
ils = IteratedLocalSearch(instance, max_iterations=100, max_time=300)
```

**Example**: For quick feasibility check:
```python
ils = IteratedLocalSearch(instance, max_iterations=10, max_time=10)
```

---

## Configuration

### Time Limits

**Edit test scripts** to change time limits:

```python
# In test_li_lim.py, line 13:
TIME_LIMIT_PER_INSTANCE = 10  # Change to 30, 60, etc.

# In test_feasibility.py, line 18:
TIME_LIMIT_PER_INSTANCE = 60  # Change as needed
```

### Number of Instances

**Run subset**:
```python
# In test_li_lim.py, modify TEST_INSTANCES list
TEST_INSTANCES = [
    "../instances/pdp_100/lc101.txt",
    "../instances/pdp_100/lc102.txt"
]
```

---

## Output Files

| File | Content | Format |
|------|---------|--------|
| `li_lim_results.json` | Detailed results for all Li & Lim instances | JSON |
| `li_lim_results.csv` | Same data in table format | CSV |
| `feasibility_test_results.json` | Results for Sartori & Buriol test | JSON |

**Open CSV in Excel**: Import as UTF-8 encoded file.

---

## Troubleshooting

### Issue: ModuleNotFoundError
```
Solution: cd algorithm && pip install -r requirements.txt
```

### Issue: "No instances found"
```
Check: ls ../instances/pdp_100/
Should see: lc101.txt, lr101.txt, etc.
```

### Issue: Test hangs or takes forever
```
Reason: Time limit too high or max_iterations too high
Solution: Reduce TIME_LIMIT_PER_INSTANCE to 10-30 seconds
```

### Issue: Results show feasible=False
```
Reason: Bug in algorithm (should never happen!)
Action: Check console for "WARNING" messages
        Review violations in output
```

### Issue: Permission denied / File not found
```
Check: Current directory is algorithm/
Run: cd algorithm before running tests
```

---

## Understanding Results

### Feasibility Status
- `feasible=True` ✓ Solution is valid
- `feasible=False` ✗ Constraint violation (bug!)

### Gap Metrics
```
gap_vehicles = (my_vehicles - best_known) / best_known * 100
gap_cost = (my_cost - best_known) / best_known * 100
```

Positive gap = your solution uses more vehicles/cost than best known.

### What "Best Known" Means
- **Li & Lim**: Solutions from literature (SINTEF TOP database)
- **Sartori**: Solutions from Sartori & Buriol (2020) paper

**Note**: If best_known=0 or missing, gap is set to 0.

---

## Next Steps

**Improve results**:
1. Increase time limit (e.g., 60s instead of 10s)
2. Increase ILS iterations (edit `max_iterations` parameter)
3. Tune LNS destroy/repair parameters (advanced)

**Add new datasets**:
1. Place `.txt` files in `instances/` directory
2. Ensure format matches Li & Lim or Sartori format
3. Parser auto-detects format

**Validate external solutions**:
```bash
cd ../validator
python validator.py -i ../instances/pdp_100/lc101.txt -s my_solution.txt
```

See `validator/README.md` for solution file format.

---

## Quick Reference

| Task | Command |
|------|---------|
| **First time setup** | `git clone ... && cd pdptw-instances/algorithm && pip install -r requirements.txt` |
| Quick test | `python test_li_lim_quick.py` |
| Full benchmark | `python test_li_lim.py` |
| Check feasibility | `python check_feasible.py` |
| Check CSV | `python check_csv.py` |
| Single instance | `python my_test.py` (create custom script) |

**All commands assume you're in the `algorithm/` directory.**

---

## Complete Workflow (From Clone to Results)

```bash
# 1. Get the code
git clone https://github.com/cssartori/pdptw-instances.git
cd pdptw-instances

# 2. Setup (optional but recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
cd algorithm
pip install -r requirements.txt

# 4. Run quick test
python test_li_lim_quick.py

# 5. Verify results
python check_feasible.py

# Done! ✓
```

**Time**: ~5 minutes for setup + quick test.

---

**Need more details?** See main [`README.md`](../README.md) at project root.
