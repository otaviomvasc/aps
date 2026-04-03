#!/usr/bin/env python3
"""
Data Consistency Checker for AMPL Healthcare Facility Location Models
Validates data for feasibility BEFORE running optimizer
"""

import re
import sys
from collections import defaultdict


def strip_comments(content: str) -> str:
    """Remove AMPL-style # comments so regexes never match commented-out lines."""
    return re.sub(r'#[^\n]*', '', content)


class DataValidator:
    def __init__(self):
        self.data = {
            'I': set(),
            'K': set(),
            'L':  defaultdict(set),   # L[k]  = EL[k] ∪ CL[k]
            'EL': defaultdict(set),   # existing facilities
            'CL': defaultdict(set),   # candidate facilities
            'W': {},
            'C1': {}, 'C2': {}, 'C3': {},
            'O1_0': {}, 'O2_0': {}, 'O3_0': {},
            'Dmax': {},
            # Distances: stored as entry-count (int) so we can report "N entries defined"
            'D0_1': 0, 'D0_2': 0, 'D0_3': 0,
        }
        self.errors = []
        self.warnings = []
        self.info = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_files(self, filenames):
        """Load all data files, then run validation once."""
        for filename in filenames:
            try:
                with open(filename, 'r') as f:
                    raw = f.read()
                content = strip_comments(raw)
                self._parse_data(content)
            except FileNotFoundError:
                print(f"❌ File not found: {filename}")
                return False

        # Build L[k] = EL[k] ∪ CL[k] after all files are parsed
        for k in [1, 2, 3]:
            self.data['L'][k] = self.data['EL'][k] | self.data['CL'][k]

        self.run_all_checks()
        return True

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_data(self, content):
        """Extract sets and parameters from comment-stripped AMPL data."""

        # --- Sets: EL[k] and CL[k] ---
        # L[k] is assembled from these after all files are loaded (see validate_files)
        for k in [1, 2, 3]:
            m = re.search(rf'set EL\[{k}\]\s*:=\s*([\s\S]*?);', content)
            if m:
                tokens = m.group(1).strip().split()
                self.data['EL'][k].update(tokens)

            m = re.search(rf'set CL\[{k}\]\s*:=\s*([\s\S]*?);', content)
            if m:
                tokens = m.group(1).strip().split()
                self.data['CL'][k].update(tokens)

        # --- Origins (set I) and demand (W) ---
        m = re.search(r'param:\s*I:\s+W\s+[^:]*:=\s*([\s\S]*?);', content)
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['W'][parts[0]] = float(parts[1])
                        self.data['I'].add(parts[0])
                    except ValueError:
                        pass

        # --- Capacities ---
        for cap_key in ('C1', 'C2', 'C3'):
            m = re.search(rf'param {cap_key}[^:]*:=\s*([\s\S]*?);', content)
            if m:
                for line in m.group(1).strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            self.data[cap_key][parts[0]] = float(parts[1])
                        except ValueError:
                            pass

        # --- Step-down ratios ---
        # Both single-column formats (param : O1_0 O1_2 O1_3 :=) are handled
        for ratio_key in ('O1_0', 'O2_0', 'O3_0'):
            m = re.search(
                rf'param\s*:\s*[\s\S]*?{ratio_key}[\s\S]*?:=\s*([\s\S]*?);',
                content,
            )
            if m:
                for line in m.group(1).strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            self.data[ratio_key][parts[0]] = float(parts[1])
                        except ValueError:
                            pass

        # --- Dmax ---
        m = re.search(r'param Dmax\[K\]\s*:=\s*([\s\S]*?);', content)
        if m:
            for line in m.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        self.data['Dmax'][int(parts[0])] = float(parts[1])
                    except ValueError:
                        pass

        # --- Distance matrices (record entry count, not values) ---
        for dist_key in ('D0_1', 'D0_2', 'D0_3'):
            m = re.search(rf'param {dist_key}[^:]*:=\s*([\s\S]*?);', content)
            if m:
                # Each entry is "origin  facility  value" → 3 tokens per pair
                tokens = m.group(1).strip().split()
                self.data[dist_key] += len(tokens) // 3

    # ------------------------------------------------------------------
    # Validation checks
    # ------------------------------------------------------------------

    def run_all_checks(self):
        """Execute all validation checks."""
        print("\n" + "=" * 80)
        print("DATA CONSISTENCY VALIDATION")
        print("=" * 80)

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
        """Verify required sets are defined."""
        print("\n[CHECK 1] Set Definitions")
        print("-" * 80)

        if not self.data['I']:
            # Only an error when demand data is also present (otherwise it is a
            # supplementary distance-only file and missing I is expected)
            if self.data['W']:
                self.errors.append("❌ Set I (origins) defined in W but not as a set")
            else:
                self.warnings.append("⚠ Set I (origins) not found — file may be distance-only")
            return

        self.info.append(f"✓ Set I: {len(self.data['I'])} origins")

        for k in [1, 2, 3]:
            lk = self.data['L'][k]
            if not lk:
                self.errors.append(
                    f"❌ Set L[{k}] (level {k} facilities) is empty — "
                    f"check set EL[{k}] and CL[{k}] definitions"
                )
            else:
                el_count = len(self.data['EL'][k])
                cl_count = len(self.data['CL'][k])
                self.info.append(
                    f"✓ Set L[{k}]: {len(lk)} facilities "
                    f"({el_count} existing, {cl_count} candidates)"
                )

    def check_parameter_indices(self):
        """Verify parameter indices match set definitions."""
        print("\n[CHECK 2] Parameter Index Consistency")
        print("-" * 80)

        # Check W indices
        if self.data['W'] and self.data['I']:
            invalid = [i for i in self.data['W'] if i not in self.data['I']]
            if invalid:
                self.errors.append(f"❌ Demand W has invalid origins: {invalid}")
            else:
                self.info.append("✓ All W indices are in set I")

        # Check capacity indices
        for cap_name, level in [('C1', 1), ('C2', 2), ('C3', 3)]:
            cap_data = self.data[cap_name]
            lk = self.data['L'][level]
            if not cap_data:
                self.info.append(f"✓ All {cap_name} indices are in set L[{level}] (none defined)")
                continue
            if not lk:
                self.errors.append(
                    f"❌ {cap_name} has entries but L[{level}] is empty — cannot validate"
                )
                continue
            invalid = [j for j in cap_data if j not in lk]
            if invalid:
                self.errors.append(f"❌ {cap_name} has invalid facilities: {invalid}")
            else:
                self.info.append(f"✓ All {cap_name} indices are in set L[{level}]")

    def check_capacity_values(self):
        """Validate capacity values are realistic."""
        print("\n[CHECK 3] Capacity Values")
        print("-" * 80)

        for cap_name, min_rec in [('C1', 500), ('C2', 1000), ('C3', 500)]:
            cap_data = self.data[cap_name]
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
        """Verify distance matrices are defined."""
        print("\n[CHECK 4] Distance Parameters")
        print("-" * 80)

        for dist_key in ('D0_1', 'D0_2', 'D0_3'):
            count = self.data[dist_key]
            if count:
                self.info.append(f"✓ {dist_key} defined ({count} entries)")
            else:
                self.warnings.append(f"⚠ {dist_key} not found")

        if self.data['Dmax']:
            self.info.append(f"✓ Dmax defined for {len(self.data['Dmax'])} levels")

    def check_step_down_ratios(self):
        """Validate patient return rates."""
        print("\n[CHECK 5] Step-Down Ratios")
        print("-" * 80)

        for ratio_name in ('O1_0', 'O2_0', 'O3_0'):
            ratio_data = self.data[ratio_name]
            if not ratio_data:
                self.warnings.append(f"⚠ {ratio_name} not found")
                continue

            min_r = min(ratio_data.values())
            max_r = max(ratio_data.values())
            avg_r = sum(ratio_data.values()) / len(ratio_data)
            self.info.append(
                f"{ratio_name}: min={min_r:.2f}, max={max_r:.2f}, avg={avg_r:.2f}"
            )

            if min_r <= 0 or max_r >= 1:
                self.warnings.append(
                    f"⚠ {ratio_name} has values outside (0, 1): "
                    f"min={min_r}, max={max_r}"
                )

    def check_demand_feasibility(self):
        """Check demand values are reasonable."""
        print("\n[CHECK 6] Demand Feasibility")
        print("-" * 80)

        if not self.data['W']:
            return

        total = sum(self.data['W'].values())
        avg   = total / len(self.data['W'])
        lo    = min(self.data['W'].values())
        hi    = max(self.data['W'].values())

        self.info.append(f"Total demand: {total}")
        self.info.append(f"Range: [{lo}, {hi}]")
        self.info.append(f"Average: {avg:.1f}")

    def check_facility_connectivity(self):
        """Report distance matrix coverage."""
        print("\n[CHECK 7] Facility Connectivity")
        print("-" * 80)

        for dist_key in ('D0_1', 'D0_2', 'D0_3'):
            count = self.data[dist_key]
            if count:
                self.info.append(f"{dist_key}: {count} distance entries defined")

    def check_network_balance(self):
        """Check if network capacity can handle required flows."""
        print("\n[CHECK 8] Network Balance")
        print("-" * 80)

        if not self.data['W'] or not self.data['C2'] or not self.data['C3']:
            return

        total_demand = sum(self.data['W'].values())
        total_c2     = sum(self.data['C2'].values())
        total_c3     = sum(self.data['C3'].values())

        # --- Cascade flow estimates ---
        if self.data['O1_0']:
            avg_o1_0 = sum(self.data['O1_0'].values()) / len(self.data['O1_0'])
        else:
            avg_o1_0 = 0.71  # default

        if self.data['O2_0']:
            avg_o2_0 = sum(self.data['O2_0'].values()) / len(self.data['O2_0'])
        else:
            avg_o2_0 = 0.65

        if self.data['O3_0']:
            avg_o3_0 = sum(self.data['O3_0'].values()) / len(self.data['O3_0'])
        else:
            avg_o3_0 = 0.80

        transfers_l1 = total_demand * (1 - avg_o1_0)
        returns_l2   = transfers_l1 * avg_o2_0
        transfers_l2 = transfers_l1 * (1 - avg_o2_0)
        returns_l3   = transfers_l2 * avg_o3_0

        self.info.append(f"Total demand:          {total_demand:.0f}")
        self.info.append(f"Total capacity: C2={total_c2:.0f}, C3={total_c3:.0f}")
        self.info.append(f"L1→L2/L3 transfers:    {transfers_l1:.0f} patients")
        self.info.append(f"L2→L3 transfers:       {transfers_l2:.0f} patients")
        self.info.append(f"L2 required capacity:  {(returns_l2 + transfers_l2):.0f}")
        self.info.append(f"L3 required capacity:  {returns_l3:.0f}")

        # L2
        if not self.data['L'][2]:
            self.errors.append("❌ No L2 facilities defined")
        elif (returns_l2 + transfers_l2) > total_c2:
            self.errors.append(
                f"❌ L2 insufficient: {(returns_l2 + transfers_l2):.0f} > {total_c2:.0f}"
            )
        else:
            self.info.append("✓ L2 capacity sufficient")

        # L3
        if not self.data['L'][3]:
            self.errors.append("❌ No L3 facilities defined")
        elif returns_l3 > total_c3:
            self.errors.append(
                f"❌ L3 insufficient: {returns_l3:.0f} > {total_c3:.0f}"
            )
        else:
            self.info.append("✓ L3 capacity sufficient")

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def print_results(self):
        """Print validation results and return exit code."""
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)

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

        print("\n" + "=" * 80)
        if self.errors:
            print("RESULT: ❌ FAILED - Fix errors before running model")
            print("=" * 80)
            return 1
        elif self.warnings:
            print("RESULT: ⚠ PASSED WITH WARNINGS")
            print("=" * 80)
            return 0
        else:
            print("RESULT: ✓ PASSED - Data is valid")
            print("=" * 80)
            return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 check_data_consistency.py <file1.dat> [file2.dat] ...")
        return 1

    validator = DataValidator()
    validator.validate_files(sys.argv[1:])
    # print_results() is already called inside run_all_checks(); return its exit code
    return 0 if not validator.errors else 1


if __name__ == "__main__":
    sys.exit(main())
