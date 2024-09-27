# 2DMAT -- Data-analysis software of quantum beam diffraction experiments for 2D material structure
# Copyright (C) 2020- The University of Tokyo
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

from sys import exit

import odatse
import odatse.mpi
import odatse.util.toml

from . import __version__
from .sim_trhepd_rheed import Solver

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Data-analysis software of quantum beam "
            "diffraction experiments for 2D material structure"
        )
    )
    parser.add_argument("inputfile", help="input file with TOML format")
    parser.add_argument("--version", action="version", version="odatse-STR {}, ODAT-SE {}".format(__version__, odatse.__version__))

    args = parser.parse_args()

    file_name = args.inputfile
    inp = {}
    if odatse.mpi.rank() == 0:
        inp = odatse.util.toml.load(file_name)
    if odatse.mpi.size() > 1:
        inp = odatse.mpi.comm().bcast(inp, root=0)
    info = odatse.Info(inp)

    algname = info.algorithm["name"]
    if algname == "mapper":
        from odatse.algorithm.mapper_mpi import Algorithm
    elif algname == "minsearch":
        from odatse.algorithm.min_search import Algorithm
    elif algname == "exchange":
        from odatse.algorithm.exchange import Algorithm
    elif algname == "pamc":
        from odatse.algorithm.pamc import Algorithm
    elif algname == "bayes":
        from odatse.algorithm.bayes import Algorithm
    else:
        print(f"ERROR: Unknown algorithm ({algname})")
        exit(1)

    solver = Solver(info)
    runner = odatse.Runner(solver, info)
    alg = Algorithm(info, runner)
    alg.main()

if __name__ == "__main__":
    main()
