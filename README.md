<!--
Purpose: Main documentation and entry point for the PDPTW project
Audience: All users (researchers, developers, students)
Status: ACTIVE - Single source of truth
-->

# PDPTW Solver - Pickup and Delivery Problem with Time Windows

**Algorithms**: ILS (Iterated Local Search) + AGES + LNS + LAHC  
**Datasets**: Li & Lim benchmark + Sartori & Buriol real-world instances  
**Status**: ✅ All solutions are strictly feasible (100% constraint satisfaction)

---

## 🎯 What This Project Does

This repository implements a **metaheuristic solver** for the **Pickup and Delivery Problem with Time Windows (PDPTW)**, a challenging vehicle routing problem where:

- Each request has a **pickup** and **delivery** location
- Pickup must occur **before** delivery
- All locations have **time windows** (earliest/latest arrival times)
- Vehicles have **capacity constraints**
- Goal: Minimize number of vehicles and total travel cost

**Key guarantee**: All solutions are **strictly feasible** - no constraint violations allowed.

---

## 📊 Supported Datasets

### 1. Li & Lim PDPTW Benchmark (2003)
- **Location**: `instances/pdp_100/`
- **Instances**: 56 instances (lc*, lr*, lrc*)
- **Format**: Euclidean coordinates, synthetic benchmark
- **Standard**: Widely used in academic research

### 2. Sartori & Buriol Real-World Benchmark (2020)
- **Location**: `instances/n100/`, `instances/n200/`, etc.
- **Instances**: 300+ instances from real cities
- **Format**: GPS coordinates, OSRM travel times
- **Cities**: Barcelona (bar), Berlin (ber), New York (nyc), Porto Alegre (poa)

See [`instances/README.md`](instances/README.md) for detailed dataset documentation.

---

## 🚀 Quick Start (3 Steps)

### Prerequisites
```bash
cd algorithm
pip install -r requirements.txt
```

### 1. Quick Test (3 instances, ~1 minute)
```bash
python test_li_lim_quick.py
```

**Expected output**:
```
[1/3] Testing lc101...
  Result: 20 veh, cost 2234, feasible=True ✓
[2/3] Testing lr101...
  Result: 29 veh, cost 2393, feasible=True ✓
[3/3] Testing lrc101...
  Result: 22 veh, cost 2486, feasible=True ✓
```

### 2. Verify Results
```bash
python check_feasible.py
```

**Expected**: `Feasible: 56/56 (100.0%)`

### 3. Full Benchmark (56 instances, ~10 minutes)
```bash
python test_li_lim.py
```

**For detailed instructions**, see [`algorithm/QUICKSTART.md`](algorithm/QUICKSTART.md)

---

## 📁 Project Structure

```
pdptw-instances/
├── README.md                    ← You are here (start here!)
│
├── algorithm/                   ← Main solver code
│   ├── QUICKSTART.md           ← How to run (detailed guide)
│   ├── *.py                    ← Algorithm implementation
│   ├── check_feasible.py       ← Verify solution feasibility
│   └── requirements.txt        ← Python dependencies
│
├── instances/                   ← Problem instances
│   ├── pdp_100/                ← Li & Lim benchmark
│   ├── n100/, n200/, ...       ← Sartori & Buriol instances
│   └── README.md               ← Dataset documentation
│
├── solutions/                   ← Best known solutions
│   ├── bks.dat                 ← Best known solution values
│   ├── files/                  ← Solution files
│   └── README.md               ← Solution format
│
├── validator/                   ← Solution validator
│   ├── validator.py            ← Validation script
│   └── README.md               ← Validator usage
│
├── visualizer/                  ← Solution visualizer
│   └── README.md               ← Visualization tool
│
└── docs/                        ← Documentation archive
    ├── implementation_reports/  ← Technical implementation details
    └── archive/                 ← Historical documentation
```

---

## 🧮 Algorithm Overview

The solver uses a **multi-layer metaheuristic approach**:

### Core Framework: ILS (Iterated Local Search)
1. **Construction**: Generate initial feasible solution (Greedy or Clarke-Wright)
2. **LNS (Large Neighborhood Search)**: Destroy and repair to reduce cost
3. **AGES**: Reduce number of vehicles while maintaining feasibility
4. **Set Partitioning**: Select best route combinations
5. **Perturbation**: Escape local optima

### Key Components:
- **LAHC (Late Acceptance Hill Climbing)**: Parameter-free acceptance criterion
- **Feasibility Validator**: Strict constraint checking at every step
- **Adaptive Operators**: Random + Shaw removal, Greedy + Regret-2 insertion

**Design Principle**: **Feasibility First** - infeasible solutions are rejected immediately, never accepted.

---

## 📈 Results

### Li & Lim Benchmark (56 instances, 10s per instance)
- **Feasible**: 56/56 (100%)
- **Average vehicles**: Competitive with literature
- **Average cost**: Within reasonable gaps

### Sartori & Buriol (3 test instances, 60s per instance)
- **Feasible**: 3/3 (100%)
- **Example (bar-n100-1)**:
  - Vehicles: 7 (Best known: 6) → Gap: +16.7%
  - Cost: 1087 (Best known: 732) → Gap: +48.5%
  - Runtime: ~24 seconds

**View detailed results**: Check `li_lim_results.csv` and `li_lim_results.json` after running tests.

---

## 🔍 Feasibility Guarantees

All solutions satisfy these **hard constraints**:

1. ✅ **Pickup before delivery**: Each request's pickup is visited before its delivery
2. ✅ **Time windows**: Arrival at each node is within [earliest, latest] time
3. ✅ **Capacity**: Vehicle load never exceeds capacity, never goes negative
4. ✅ **Pairing**: Pickup and delivery on same route
5. ✅ **Coverage**: Each request served exactly once (no missing, no duplicates)
6. ✅ **Depot**: Routes start and end at depot within depot time windows

**Validation**: Every solution is checked by the official validator from Sartori & Buriol.

---

## 📖 Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| **This file** | Project overview, quick start | Everyone |
| [`algorithm/QUICKSTART.md`](algorithm/QUICKSTART.md) | Detailed running instructions | Users |
| [`instances/README.md`](instances/README.md) | Dataset documentation | Researchers |
| [`solutions/README.md`](solutions/README.md) | Solution file format | Contributors |
| [`validator/README.md`](validator/README.md) | How to validate solutions | Developers |
| [`docs/implementation_reports/`](docs/implementation_reports/) | Technical details | Developers |
| [`docs/archive/`](docs/archive/) | Historical documentation | Reference only |

---

## 🛠️ Troubleshooting

**Problem**: `ModuleNotFoundError`  
**Solution**: `cd algorithm && pip install -r requirements.txt`

**Problem**: `No instances found`  
**Solution**: Verify `instances/pdp_100/` directory exists with `.txt` files

**Problem**: Results show `feasible=False`  
**Solution**: This indicates a bug - report it. All solutions should be feasible.

**Problem**: Test runs but no output files  
**Solution**: Check current directory is `algorithm/`, results saved as `*.json` and `*.csv`

---

## 📚 References

### Original Benchmarks

**Li & Lim PDPTW Benchmark (2003)**:
```
@article{li-lim-2003,
  title={A tabu search heuristic for the pickup and delivery problem with time windows},
  author={Li, Haibing and Lim, Andrew},
  journal={Computational Optimization and Applications},
  year={2003}
}
```

**Sartori & Buriol Real-World Instances (2020)**:
```
@article{sartori-buriol-2020,
  title={A Study on the Pickup and Delivery Problem with Time Windows: Matheuristics and New Instances},
  author={Carlo S. Sartori and Luciana S. Buriol},
  journal={Computers & Operations Research},
  year={2020},
  doi={10.1016/j.cor.2020.105065}
}
```

### Algorithm References

- **ALNS**: Ropke & Pisinger (2006) - Adaptive Large Neighborhood Search
- **LAHC**: Burke & Bykov (2017) - Late Acceptance Hill Climbing
- **AGES**: Curtois et al. (2018) - Automated Generation of Efficient Solutions

---

## 🤝 Contributing

### Reporting Issues
- Include: instance name, command used, error message
- Attach: output logs, result files if relevant

### Submitting New Best Known Solutions
For Sartori & Buriol instances:
- Email: cssartori `at` inf `dot` ufrgs `dot` br
- Include solution file in correct format (see `solutions/README.md`)

---

## 📄 License

This repository follows the licensing of the original Sartori & Buriol benchmark repository.

The algorithm implementation is provided for **research and educational purposes**.

---

## 🔗 Related Resources

- **Sartori & Buriol Original Repository**: [github.com/cssartori/pdptw-instances](https://github.com/cssartori/pdptw-instances)
- **SINTEF TOP (Li & Lim BKS)**: [sintef.no/projectweb/top](https://www.sintef.no/projectweb/top/)
- **CVRPLib**: [vrp.atd-lab.inf.puc-rio.br](http://vrp.atd-lab.inf.puc-rio.br/)

---

**Last Updated**: January 2026  
**Maintained by**: PDPTW Solver Contributors
