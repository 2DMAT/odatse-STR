import numpy as np

import odatse
import odatse.algorithm.min_search
from odatse.extra.STR import Solver

params = {
    "base": {
        "dimension": 3,
        "output_dir": "output",
    },
    "solver": {
        "run_scheme": "subprocess",
        "generate_rocking_curve": True,
        "config": {
            "cal_number": [1],
        },
        "param": {
            "string_list": ["value_01", "value_02", "value_03"],
        },
        "reference": {
            "path": "experiment.txt",
            "exp_number": [1],
        },
        "post": {
            "normalization": "TOTAL",
        },
    },
    "algorithm": {
        "label_list": ["z1", "z2", "z3"],
        "param": {
            "min_list": [ 0.0, 0.0, 0.0 ],
            "max_list": [ 10.0, 10.0, 10.0 ],
            "initial_list": [ 5.25, 4.25, 3.50],
        },
    },
}

info = odatse.Info(params)

solver = Solver(info)

runner = odatse.Runner(solver, info)

alg = odatse.algorithm.min_search.Algorithm(info, runner)

alg.main()
