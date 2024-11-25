import os
import sys
import pytest
from pydantic import ValidationError

SOURCE_PATH = os.path.join(os.path.dirname(__file__), '../../src')
sys.path.append(SOURCE_PATH)

class switch_dir:
    def __init__(self, d):
        self.d = d
    def __enter__(self):
        self.owd = os.getcwd()
        os.chdir(self.d)
        return self
    def __exit__(self, ex_type, ex_value, tb):
        os.chdir(self.owd)
        return ex_type is None


def test_write_input_file():
    import odatse
    from STR.input import Input
    from STR.parameter import SolverInfo
    import shutil
    from tempfile import TemporaryDirectory
    import tomli

    solver_input = """
    [solver]
    dimension = 2
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["value_01", "value_02"]
    [solver.reference]
    exp_number = [1]
    """

    xval = [0.1, 0.2]
    arg = (0, 0)

    test_dir = os.path.dirname(__file__)

    with TemporaryDirectory() as work_dir:
        with switch_dir(work_dir):
            shutil.copy(os.path.join(test_dir, "template.txt"), "template.txt")
            shutil.copy(os.path.join(test_dir, "bulkP.b"), "bulkP.b")

            solver_params = tomli.loads(solver_input)
            solver_info = SolverInfo(**solver_params["solver"])

            info = odatse.Info({'base': {}, 'algorithm': {}, 'solver': {}})

            input = Input(info.base, solver_info, False, {})

            input.prepare(xval, arg)

            data_dir = "Log{:08d}_{:08d}".format(arg[0], arg[1])

            with open(os.path.join(data_dir, "surf.txt"), "r") as f:
                surf_txt = f.readlines()
            with open(os.path.join(test_dir, "surf_ref.txt"), "r") as f:
                surf_ref = f.readlines()

            for i, (a, b) in enumerate(zip(surf_ref, surf_txt)):
                assert a == b, "line {} differs".format(i)

            with open(os.path.join(data_dir, "bulkP.b"), "rb") as f:
                bulkP_dat = f.read()
            with open(os.path.join(test_dir, "bulkP.b"), "rb") as f:
                bulkP_ref = f.read()

            assert bulkP_ref == bulkP_dat, "bulkP.b not identical"

        

def test_get_results():
    import odatse
    from STR.output import Output
    from STR.parameter import SolverInfo
    import shutil
    from tempfile import TemporaryDirectory
    import tomli
    import numpy as np

    solver_input = """
    [solver]
    dimension = 2
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["value_01", "value_02"]
    [solver.reference]
    exp_number = [1]
    """
    # with open(os.path.join(test_dir, "input.toml"), "rb") as f:
    #     solver_input = tomli.load(f)

    xval = [5.25, 4.25]
    arg = (0, 0)
    fval = 0.015197203449856747
    
    test_dir = os.path.dirname(__file__)

    with TemporaryDirectory() as work_dir:
        with switch_dir(work_dir):
            mpirank = odatse.mpi.rank()
            data_dir = os.path.join("Log{:08d}_{:08d}".format(arg[0], arg[1]), str(mpirank))

            shutil.copy(os.path.join(test_dir, "experiment.txt"), "experiment.txt")

            os.makedirs(data_dir)
            shutil.copy(os.path.join(test_dir, "surf-bulkP.s_ref"), os.path.join(data_dir, "surf-bulkP.s"))

            solver_params = tomli.loads(solver_input)
            solver_info = SolverInfo(**solver_params["solver"])

            info = odatse.Info({'base': {}, 'algorithm': {}, 'solver': {}})

            output = Output(info.base, solver_info, False, {})

            with switch_dir(data_dir):
                output.prepare(xval)
                v = output.get_results(".")
            
            assert np.isclose(v, fval)
