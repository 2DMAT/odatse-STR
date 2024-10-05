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
import importlib

import odatse

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

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--init", action="store_true", help="initial start (default)")
    mode_group.add_argument("--resume", action="store_true", help="resume intterupted run")
    mode_group.add_argument("--cont", action="store_true", help="continue from previous run")

    parser.add_argument("--reset_rand", action="store_true", default=False, help="new random number series in resume or continue mode")

    args = parser.parse_args()

    file_name = args.inputfile
    info = odatse.Info.from_file(file_name)

    alg_table = {
        "mapper": "mapper_mpi",
    }

    if "name" not in info.algorithm:
        print("ERROR: algorithm.name not defined")
        exit(1)
    try:
        aname = info.algorithm["name"]
        algname = "odatse.algorithm.{}".format(alg_table.get(aname, aname))
        algmod = importlib.import_module(algname)
    except ModuleNotFoundError as e:
        print("ERROR: {}".format(e, algname))
        exit(1)

    if args.init is True:
        run_mode = "initial"
    elif args.resume is True:
        run_mode = "resume"
        if args.reset_rand is True:
            run_mode = "resume-resetrand"
    elif args.cont is True:
        run_mode = "continue"
        if args.reset_rand is True:
            run_mode = "continue-resetrand"
    else:
        run_mode = "initial"  # default

    solver = Solver(info)
    runner = odatse.Runner(solver, info)
    alg = algmod.Algorithm(info, runner, run_mode=run_mode)
    result = alg.main()

if __name__ == "__main__":
    main()
