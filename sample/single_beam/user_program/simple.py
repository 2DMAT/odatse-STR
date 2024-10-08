import numpy as np

import py2dmat
import py2dmat.algorithm.min_search
from odatse.extra.sim_trhepd_rheed import Solver

info = py2dmat.Info.from_file("input.toml")

solver = Solver(info)

runner = py2dmat.Runner(solver, info)

alg = py2dmat.algorithm.min_search.Algorithm(info, runner)

alg.main()
