"""
Best Known Solutions (BKS) for Li & Lim PDPTW Benchmark

Sources:
- Li & Lim (2003): Original paper
- SINTEF TOP: https://www.sintef.no/projectweb/top/pdptw/li-lim-benchmark/
- Various publications (Ropke & Pisinger 2006, Curtois et al 2018)

Note: Cost = total distance (Euclidean)
"""

LI_LIM_BKS = {
    # LC1 instances (short scheduling horizon, tight time windows)
    'lc101': {'vehicles': 10, 'cost': 828.94},
    'lc102': {'vehicles': 10, 'cost': 828.94},
    'lc103': {'vehicles': 9, 'cost': 828.06},
    'lc104': {'vehicles': 9, 'cost': 824.78},
    'lc105': {'vehicles': 10, 'cost': 828.94},
    'lc106': {'vehicles': 10, 'cost': 828.94},
    'lc107': {'vehicles': 10, 'cost': 828.94},
    'lc108': {'vehicles': 10, 'cost': 828.94},
    'lc109': {'vehicles': 9, 'cost': 828.06},
    
    # LC2 instances (long scheduling horizon, tight time windows)
    'lc201': {'vehicles': 3, 'cost': 591.56},
    'lc202': {'vehicles': 3, 'cost': 591.56},
    'lc203': {'vehicles': 3, 'cost': 591.17},
    'lc204': {'vehicles': 3, 'cost': 590.60},
    'lc205': {'vehicles': 3, 'cost': 588.88},
    'lc206': {'vehicles': 3, 'cost': 588.49},
    'lc207': {'vehicles': 3, 'cost': 588.29},
    'lc208': {'vehicles': 3, 'cost': 588.32},
    
    # LR1 instances (short scheduling horizon, loose time windows)
    'lr101': {'vehicles': 19, 'cost': 1650.80},
    'lr102': {'vehicles': 17, 'cost': 1487.57},
    'lr103': {'vehicles': 13, 'cost': 1292.68},
    'lr104': {'vehicles': 9, 'cost': 1013.39},
    'lr105': {'vehicles': 14, 'cost': 1377.11},
    'lr106': {'vehicles': 12, 'cost': 1252.62},
    'lr107': {'vehicles': 10, 'cost': 1111.31},
    'lr108': {'vehicles': 9, 'cost': 968.97},
    'lr109': {'vehicles': 11, 'cost': 1208.96},
    'lr110': {'vehicles': 10, 'cost': 1159.35},
    'lr111': {'vehicles': 10, 'cost': 1108.90},
    'lr112': {'vehicles': 9, 'cost': 1003.77},
    
    # LR2 instances (long scheduling horizon, loose time windows)
    'lr201': {'vehicles': 4, 'cost': 1253.23},
    'lr202': {'vehicles': 3, 'cost': 1197.67},
    'lr203': {'vehicles': 3, 'cost': 949.40},
    'lr204': {'vehicles': 2, 'cost': 825.52},
    'lr205': {'vehicles': 3, 'cost': 1054.02},
    'lr206': {'vehicles': 3, 'cost': 931.63},
    'lr207': {'vehicles': 2, 'cost': 903.06},
    'lr208': {'vehicles': 2, 'cost': 734.85},
    'lr209': {'vehicles': 3, 'cost': 930.59},
    'lr210': {'vehicles': 3, 'cost': 964.22},
    'lr211': {'vehicles': 2, 'cost': 885.71},
    
    # LRC1 instances (short scheduling horizon, mixed time windows)
    'lrc101': {'vehicles': 14, 'cost': 1708.80},
    'lrc102': {'vehicles': 12, 'cost': 1558.07},
    'lrc103': {'vehicles': 11, 'cost': 1258.74},
    'lrc104': {'vehicles': 10, 'cost': 1128.40},
    'lrc105': {'vehicles': 13, 'cost': 1637.62},
    'lrc106': {'vehicles': 11, 'cost': 1424.73},
    'lrc107': {'vehicles': 11, 'cost': 1230.14},
    'lrc108': {'vehicles': 10, 'cost': 1147.43},
    
    # LRC2 instances (long scheduling horizon, mixed time windows)
    'lrc201': {'vehicles': 4, 'cost': 1406.94},
    'lrc202': {'vehicles': 3, 'cost': 1374.27},
    'lrc203': {'vehicles': 3, 'cost': 1089.07},
    'lrc204': {'vehicles': 3, 'cost': 818.66},
    'lrc205': {'vehicles': 4, 'cost': 1302.20},
    'lrc206': {'vehicles': 3, 'cost': 1159.03},
    'lrc207': {'vehicles': 3, 'cost': 1062.05},
    'lrc208': {'vehicles': 3, 'cost': 852.76},
}


def get_bks(instance_name):
    """
    Get Best Known Solution for a Li & Lim instance
    
    Args:
        instance_name: Instance name (e.g., 'lc101', 'lr201')
    
    Returns:
        dict with 'vehicles' and 'cost', or None if not found
    """
    return LI_LIM_BKS.get(instance_name.lower(), None)


def calculate_gap(my_value, bks_value):
    """
    Calculate percentage gap from BKS
    
    Args:
        my_value: Solution value
        bks_value: Best known value
    
    Returns:
        Gap percentage (positive = worse than BKS)
    """
    if bks_value == 0:
        return 0.0
    return ((my_value - bks_value) / bks_value) * 100.0


if __name__ == "__main__":
    # Test BKS database
    print("Li & Lim BKS Database")
    print("=" * 60)
    
    print("\nLC1 instances:")
    for inst in ['lc101', 'lc102', 'lc103', 'lc104']:
        bks = get_bks(inst)
        print(f"  {inst}: {bks['vehicles']} veh, {bks['cost']:.2f} cost")
    
    print("\nLC2 instances:")
    for inst in ['lc201', 'lc202', 'lc203', 'lc204']:
        bks = get_bks(inst)
        print(f"  {inst}: {bks['vehicles']} veh, {bks['cost']:.2f} cost")
    
    print(f"\nTotal instances in database: {len(LI_LIM_BKS)}")
