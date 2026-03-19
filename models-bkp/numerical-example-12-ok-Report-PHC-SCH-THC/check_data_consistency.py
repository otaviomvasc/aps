#!/usr/bin/env python3
"""
Data Consistency Checker for AMPL Healthcare Facility Location Models
Validates data for feasibility BEFORE running optimizer
"""

import re
import sys
from collections import defaultdict

class DataValidator:
    def __init__(self):
        self.data = {
            'I': set(),
            'K': set(),
            'L': defaultdict(set),
            'EL': defaultdict(set),
            'W': {},
            'C1': {}, 'C2': {}, 'C3': {},
            'O1_0': {}, 'O2_0': {}, 'O3_0': {},
            'Dmax': {},
            'D0_1': [], 'D0_2': [], 'D0_3': [],
        }
        self.errors = []
        self.warnings = []
        self.info = []

    def validate_files(self, filenames):
        """Load and validate all data files"""
        for filename in filenames:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self._parse_data(content)
            except FileNotFoundError:
                print(f"❌ File not found: {filename}")
                return False
        
        self.run_all_checks()
        return True

    def _parse_data(self, content):
        """Extract sets and parameters from AMPL data"""
        # Sets
        for k in [1, 2, 3]:
            match = re.search(rf'set L\[{k}\]\s*:=\s*([\s\S]*?);', content)
            if match:
                self.data['L'][k] = set(match.group(1).strip().split())
            
            match = re.search(rf'set EL\[{k}\]\s*:=\s*([\s\S]*?);', content)
            if match:
                self.data['EL'][k] = set(match.group(1).strip().split())
        
        # Origins and demand
        match = re.search(r'param:\s*I:\s+W\s+[^:]*:=\s*([\s\S]*?);', content)
        if match:
            for line in match.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['W'][parts[0]] = float(parts[1])
                        self.data['I'].add(parts[0])
                    except:
                        pass
        
        # Capacities
        for cap, key in [('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3')]:
            match = re.search(rf'param {cap}[^:]*:=\s*([\s\S]*?);', content)
            if match:
                for line in match.group(1).strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            self.data[key][parts[0]] = float(parts[1])
                        except:
                            pass
        
        # Step-down ratios (handle BOTH formats)
        # Format 1: param: O1_0 O1_2 O1_3 :=
        # Format 2: param \n: O1_0 O1_2 O1_3 :=
        
        # More flexible regex to handle colon on same line OR next line
        # Matches: param (whitespace/newline) : (anything) O1_0 (anything) :=
        
        match = re.search(r'param\s*:\s*[\s\S]*?O1_0[\s\S]*?:=\s*([\s\S]*?);', content)
        if match:
            for line in match.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['O1_0'][parts[0]] = float(parts[1])
                    except:
                        pass
        
        match = re.search(r'param\s*:\s*[\s\S]*?O2_0[\s\S]*?:=\s*([\s\S]*?);', content)
        if match:
            for line in match.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['O2_0'][parts[0]] = float(parts[1])
                    except:
                        pass
        
        match = re.search(r'param\s*:\s*[\s\S]*?O3_0[\s\S]*?:=\s*([\s\S]*?);', content)
        if match:
            for line in match.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['O3_0'][parts[0]] = float(parts[1])
                    except:
                        pass
        
        # Dmax
        match = re.search(r'param Dmax\[K\]\s*:=\s*([\s\S]*?);', content)
        if match:
            for line in match.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['Dmax'][int(parts[0])] = float(parts[1])
                    except:
                        pass
        
        # Distances
        for dist, key in [('D0_1', 'D0_1'), ('D0_2', 'D0_2'), ('D0_3', 'D0_3')]:
            match = re.search(rf'param {dist}[^:]*:=\s*([\s\S]*?);', content)
            if match:
                count = len(match.group(1).strip().split())
                self.data[key] = [None] * count

    def run_all_checks(self):
        """Execute all validation checks"""
        print("\n" + "="*80)
        print("DATA CONSISTENCY VALIDATION")
        print("="*80)
        
        self.check_set_definitions()
        self.check_parameter_indices()
        self.check_capacity_values()
        self.check_distance_parameters()
        self.check_step_down_ratios()
        self.check_demand_feasibility()
        self.check_facility_connectivity()
        self.check_network_balance()
        
        self.print_results()

    def check_set_definitions(self):
        """Verify required sets are defined"""
        print("\n[CHECK 1] Set Definitions")
        print("-" * 80)
        
        if not self.data['I']:
            self.errors.append("❌ Set I (origins) not found")
            return
        
        self.info.append(f"✓ Set I: {len(self.data['I'])} origins")
        
        for k in [1, 2, 3]:
            if not self.data['L'][k]:
                self.errors.append(f"❌ Set L[{k}] (level {k} facilities) not found")
            else:
                self.info.append(f"✓ Set L[{k}]: {len(self.data['L'][k])} facilities")
                
                el_count = len(self.data['EL'][k])
                self.info.append(f"  - {el_count} existing, {len(self.data['L'][k]) - el_count} candidates")

    def check_parameter_indices(self):
        """Verify parameter indices match set definitions"""
        print("\n[CHECK 2] Parameter Index Consistency")
        print("-" * 80)
        
        # Check W indices
        invalid = [i for i in self.data['W'] if i not in self.data['I']]
        if invalid:
            self.errors.append(f"❌ Demand W has invalid origins: {invalid}")
        else:
            self.info.append("✓ All W indices are in set I")
        
        # Check capacity indices
        for cap_name, cap_data, level in [('C1', self.data['C1'], 1), 
                                          ('C2', self.data['C2'], 2), 
                                          ('C3', self.data['C3'], 3)]:
            invalid = [j for j in cap_data if j not in self.data['L'][level]]
            if invalid:
                self.errors.append(f"❌ {cap_name} has invalid facilities: {invalid}")
            else:
                self.info.append(f"✓ All {cap_name} indices are in set L[{level}]")

    def check_capacity_values(self):
        """Validate capacity values are realistic"""
        print("\n[CHECK 3] Capacity Values")
        print("-" * 80)
        
        if not self.data['W']:
            return
        
        max_demand = max(self.data['W'].values())
        
        for cap_name, cap_data, min_rec in [('C1', self.data['C1'], 500),
                                            ('C2', self.data['C2'], 1000),
                                            ('C3', self.data['C3'], 500)]:
            if not cap_data:
                continue
            
            min_cap = min(cap_data.values())
            max_cap = max(cap_data.values())
            
            self.info.append(f"{cap_name}: min={min_cap}, max={max_cap}")
            
            if min_cap < 100:
                self.errors.append(
                    f"❌ {cap_name} capacity unrealistically small (min={min_cap}). "
                    f"Recommend {cap_name} >= {min_rec}."
                )

    def check_distance_parameters(self):
        """Verify distance matrices are defined"""
        print("\n[CHECK 4] Distance Parameters")
        print("-" * 80)
        
        for dist, key in [('D0_1', 'D0_1'), ('D0_2', 'D0_2'), ('D0_3', 'D0_3')]:
            if self.data[key]:
                self.info.append(f"✓ {dist} defined ({len(self.data[key])} entries)")
            else:
                self.warnings.append(f"⚠ {dist} not found")
        
        if self.data['Dmax']:
            self.info.append(f"✓ Dmax defined for {len(self.data['Dmax'])} levels")

    def check_step_down_ratios(self):
        """Validate patient return rates"""
        print("\n[CHECK 5] Step-Down Ratios")
        print("-" * 80)
        
        for ratio_name, ratio_data in [('O1_0', self.data['O1_0']),
                                       ('O2_0', self.data['O2_0']),
                                       ('O3_0', self.data['O3_0'])]:
            if not ratio_data:
                self.warnings.append(f"⚠ {ratio_name} not found")
                continue
            
            min_r = min(ratio_data.values())
            max_r = max(ratio_data.values())
            avg_r = sum(ratio_data.values()) / len(ratio_data)
            
            self.info.append(f"{ratio_name}: min={min_r:.2f}, max={max_r:.2f}, avg={avg_r:.2f}")
            
            if min_r <= 0 or max_r >= 1:
                self.warnings.append(
                    f"⚠ {ratio_name} has values outside (0, 1): min={min_r}, max={max_r}"
                )

    def check_demand_feasibility(self):
        """Check demand values are reasonable"""
        print("\n[CHECK 6] Demand Feasibility")
        print("-" * 80)
        
        if not self.data['W']:
            return
        
        total_demand = sum(self.data['W'].values())
        avg_demand = total_demand / len(self.data['W'])
        min_demand = min(self.data['W'].values())
        max_demand = max(self.data['W'].values())
        
        self.info.append(f"Total demand: {total_demand}")
        self.info.append(f"Range: [{min_demand}, {max_demand}]")
        self.info.append(f"Average: {avg_demand:.1f}")

    def check_facility_connectivity(self):
        """Verify distance matrix coverage"""
        print("\n[CHECK 7] Facility Connectivity")
        print("-" * 80)
        
        if self.data['D0_1']:
            coverage_1 = len([x for x in self.data['D0_1'] if x])
            self.info.append(f"D0_1 coverage: {coverage_1}/{len(self.data['D0_1'])}")
        
        if self.data['D0_2']:
            coverage_2 = len([x for x in self.data['D0_2'] if x])
            self.info.append(f"D0_2 coverage: {coverage_2}/{len(self.data['D0_2'])}")
        
        if self.data['D0_3']:
            coverage_3 = len([x for x in self.data['D0_3'] if x])
            self.info.append(f"D0_3 coverage: {coverage_3}/{len(self.data['D0_3'])}")

    def check_network_balance(self):
        """Check if network capacity can handle required flows"""
        print("\n[CHECK 8] Network Balance")
        print("-" * 80)
        
        if not self.data['W'] or not self.data['C2'] or not self.data['C3']:
            return
        
        total_demand = sum(self.data['W'].values())
        total_c2 = sum(self.data['C2'].values())
        total_c3 = sum(self.data['C3'].values())
        
        el2_count = len(self.data['EL'][2])
        cl2_count = len(self.data['L'][2]) - el2_count
        el3_count = len(self.data['EL'][3])
        cl3_count = len(self.data['L'][3]) - el3_count
        
        self.info.append(f"Total demand: {total_demand}")
        self.info.append(f"Total capacity: C2={total_c2}, C3={total_c3}")
        
        # Calculate flows through cascade
        if self.data['O1_0']:
            avg_o1_0 = sum(self.data['O1_0'].values()) / len(self.data['O1_0'])
            transfers_l1 = total_demand * (1 - avg_o1_0)
        else:
            transfers_l1 = total_demand * 0.29
        
        if self.data['O2_0']:
            avg_o2_0 = sum(self.data['O2_0'].values()) / len(self.data['O2_0'])
            transfers_l2 = transfers_l1 * (1 - avg_o2_0)
            returns_l2 = transfers_l1 * avg_o2_0
        else:
            transfers_l2 = transfers_l1 * 0.35
            returns_l2 = transfers_l1 * 0.65
        
        if self.data['O3_0']:
            avg_o3_0 = sum(self.data['O3_0'].values()) / len(self.data['O3_0'])
            returns_l3 = transfers_l2 * avg_o3_0
        else:
            returns_l3 = transfers_l2 * 0.80
        
        self.info.append(f"\nL1→L2/L3: {transfers_l1:.0f} patients")
        self.info.append(f"L2→L3: {transfers_l2:.0f} patients")
        self.info.append(f"L2 required capacity: {(returns_l2 + transfers_l2):.0f}")
        self.info.append(f"L3 required capacity: {returns_l3:.0f}")
        
        # Check feasibility
        if el2_count + cl2_count == 0:
            self.errors.append("❌ No L2 facilities defined")
        elif (returns_l2 + transfers_l2) > total_c2:
            self.errors.append(
                f"❌ L2 insufficient: {(returns_l2 + transfers_l2):.0f} > {total_c2}"
            )
        else:
            self.info.append(f"✓ L2 capacity sufficient")
        
        if el3_count + cl3_count == 0:
            self.errors.append("❌ No L3 facilities defined")
        elif returns_l3 > total_c3:
            self.errors.append(
                f"❌ L3 insufficient: {returns_l3:.0f} > {total_c3}"
            )
        else:
            self.info.append(f"✓ L3 capacity sufficient")

    def print_results(self):
        """Print validation results"""
        print("\n" + "="*80)
        print("VALIDATION RESULTS")
        print("="*80)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            print("-" * 80)
            for i, err in enumerate(self.errors, 1):
                print(f"{i}. {err}")
        
        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)}):")
            print("-" * 80)
            for i, warn in enumerate(self.warnings, 1):
                print(f"{i}. {warn}")
        
        if self.info:
            print(f"\n✓ INFO ({len(self.info)}):")
            print("-" * 80)
            for i, inf in enumerate(self.info, 1):
                print(f"{i}. {inf}")
        
        print("\n" + "="*80)
        if self.errors:
            print("RESULT: ❌ FAILED - Fix errors before running model")
            print("="*80)
            return 1
        elif self.warnings:
            print("RESULT: ⚠ PASSED WITH WARNINGS")
            print("="*80)
            return 0
        else:
            print("RESULT: ✓ PASSED - Data is valid")
            print("="*80)
            return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_data_consistency.py <file1.dat> [file2.dat] ...")
        return 1
    
    validator = DataValidator()
    if validator.validate_files(sys.argv[1:]):
        return validator.print_results()
    return 1

if __name__ == "__main__":
    sys.exit(main())
