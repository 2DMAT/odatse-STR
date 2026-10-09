# odatse-STR -- SIM-TRHEPD-RHEED solver module for ODAT-SE
# Copyright (C) 2024- The University of Tokyo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

"""
Compare two text files of numerical results with a tolerance.

usage: almost_diff.py [-e EPS] [-a ABS] file1 file2

Comment lines (starting with '#') and blank lines are ignored, so that
header or footer lines added by newer versions of ODAT-SE do not affect
the comparison. The remaining lines are compared token by token:
identical strings and equal integers always match; floating-point
values match when

    |a - b| / (|a| + |b|) < EPS,   or   |a| < ABS and |b| < ABS.

Non-numerical tokens must match exactly. The exit status is 0 when the
files agree and 1 otherwise.
"""

import argparse
import math
import sys


def load(filename):
    rows = []
    with open(filename, "r") as fp:
        for line in fp:
            s = line.strip()
            if s == "" or s.startswith("#"):
                continue
            rows.append(s.split())
    return rows


def tokens_match(va, vb, eps, abs_eps):
    if va == vb:
        return True
    try:
        return int(va) == int(vb)
    except ValueError:
        pass
    try:
        fa = float(va)
        fb = float(vb)
    except ValueError:
        return False
    if math.isnan(fa) and math.isnan(fb):
        return True
    if math.isinf(fa) or math.isinf(fb):
        return fa == fb
    if abs(fa) < abs_eps and abs(fb) < abs_eps:
        return True
    return abs(fa - fb) / (abs(fa) + abs(fb)) < eps


def main():
    parser = argparse.ArgumentParser(description="compare numerical result files with a tolerance")
    parser.add_argument("file1")
    parser.add_argument("file2")
    parser.add_argument("-e", "--eps", type=float, default=1.0e-8, help="relative tolerance (default: 1e-8)")
    parser.add_argument("-a", "--abs", type=float, default=1.0e-12, help="values below this magnitude are treated as zero (default: 1e-12)")
    args = parser.parse_args()

    rows_a = load(args.file1)
    rows_b = load(args.file2)

    err = 0
    if len(rows_a) != len(rows_b):
        print("DIFF: number of data lines differ: {} {}".format(len(rows_a), len(rows_b)))
        err += 1

    for idx, (ra, rb) in enumerate(zip(rows_a, rows_b)):
        if len(ra) != len(rb):
            print("DIFF: line {}: number of fields differ: {} {}".format(idx, len(ra), len(rb)))
            err += 1
            continue
        for va, vb in zip(ra, rb):
            if not tokens_match(va, vb, args.eps, args.abs):
                print("DIFF: line {}: {} {}".format(idx, va, vb))
                err += 1

    sys.exit(1 if err > 0 else 0)


if __name__ == "__main__":
    main()
