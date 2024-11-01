import itertools
import os
import os.path
import shutil
import time
import ctypes
import subprocess

import numpy as np

import odatse
from odatse import exception, mpi
from .input import Input
from .output import Output

# for type hints
from pathlib import Path
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mpi4py import MPI


class Solver(odatse.solver.SolverBase):
    """
    Solver class for sim_trhepd_rheed.

    Attributes
    ----------
    mpicomm : Optional["MPI.Comm"]
        MPI communicator.
    mpisize : int
        Size of the MPI communicator.
    mpirank : int
        Rank of the MPI communicator.
    run_scheme : str
        Scheme to run the solver, either 'subprocess' or 'connect_so'.
    isLogmode : bool
        Flag to indicate if logging mode is enabled.
    detail_timer : Dict
        Dictionary to store detailed timing information.
    path_to_solver : Path
        Path to the solver executable.
    """

    def __init__(self, info: odatse.Info):
        """
        Initialize the Solver.

        Parameters
        ----------
        info : odatse.Info
            Information object containing solver configuration.
        """
        super().__init__(info)

        self.mpicomm = mpi.comm()
        self.mpisize = mpi.size()
        self.mpirank = mpi.rank()

        self._name = "sim_trhepd_rheed_mb_connect"

        self.run_scheme = info.solver.get("run_scheme", "subprocess")
        scheme_list = ["subprocess", "connect_so"]

        if self.run_scheme not in scheme_list:
            raise exception.InputError("ERROR : solver.run_scheme should be 'subprocess' or 'connect_so'.")

        if self.run_scheme == "connect_so":
            self.load_so()

        elif self.run_scheme == "subprocess":
            # path to surf.exe
            p2solver = info.solver["config"].get("surface_exec_file", "surf.exe")
            if os.path.dirname(p2solver) != "":
                # ignore ENV[PATH]
                self.path_to_solver = self.root_dir / Path(p2solver).expanduser()
            else:
                for P in itertools.chain(
                    [self.root_dir], os.environ["PATH"].split(":")
                ):
                    self.path_to_solver = Path(P) / p2solver
                    if os.access(self.path_to_solver, mode=os.X_OK):
                        break
            if not os.access(self.path_to_solver, mode=os.X_OK):
                raise exception.InputError(f"ERROR: solver ({p2solver}) is not found")

        self.isLogmode = False
        self.set_detail_timer()

        self.input = Input(info, self.isLogmode, self.detail_timer)
        self.output = Output(info, self.isLogmode, self.detail_timer)

    def set_detail_timer(self) -> None:
        """
        Set the detail timer for logging mode.
        """
        if self.isLogmode:
            self.detail_timer = {}
            self.detail_timer["prepare_Log-directory"] = 0
            self.detail_timer["make_surf_input"] = 0
            self.detail_timer["launch_STR"] = 0
            self.detail_timer["load_STR_result"] = 0
            self.detail_timer["convolution"] = 0
            self.detail_timer["normalize_calc_I"] = 0
            self.detail_timer["calculate_R-factor"] = 0
            self.detail_timer["make_RockingCurve.txt"] = 0
            self.detail_timer["delete_Log-directory"] = 0
        else:
            self.detail_timer = {}

    def default_run_scheme(self) -> str:
        """
        Get the default run scheme.

        Returns
        -------
        str
            The run scheme.
        """
        return self.run_scheme

    def command(self) -> List[str]:
        """
        Get the command to invoke the solver.

        Returns
        -------
        List[str]
            The command to invoke the solver.
        """
        return [str(self.path_to_solver)]

    def evaluate(self, x: np.ndarray, args=(), nprocs: int = 1, nthreads: int = 1) -> float:
        """
        Evaluate the solver with given parameters.

        Parameters
        ----------
        x : np.ndarray
            Input array.
        args : tuple, optional
            Additional arguments.
        nprocs : int, optional
            Number of processes.
        nthreads : int, optional
            Number of threads.

        Returns
        -------
        float
            The evaluation result.
        """
        self.prepare(x, args)
        cwd = os.getcwd()
        os.chdir(self.work_dir)
        self.run(nprocs, nthreads)
        os.chdir(cwd)
        result = self.get_results()
        return result

    def prepare(self, x: np.ndarray, args) -> None:
        """
        Prepare the solver for evaluation.

        Parameters
        ----------
        x : np.ndarray
            Input array.
        args : tuple
            Additional arguments.
        """
        fitted_x_list, subdir = self.input.prepare(x, args)
        self.work_dir = self.proc_dir / Path(subdir)

        self.output.prepare(fitted_x_list)

    def get_results(self) -> float:
        """
        Get the results from the solver.

        Returns
        -------
        float
            The result.
        """
        return self.output.get_results(self.work_dir)

    def load_so(self) -> None:
        """
        Load the shared object library for the solver.
        """
        self.lib = np.ctypeslib.load_library("surf.so", os.path.dirname(__file__))
        self.lib.surf_so.argtypes = (
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            np.ctypeslib.ndpointer(),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
            np.ctypeslib.ndpointer(),
            np.ctypeslib.ndpointer(),
        )
        self.lib.surf_so.restype = ctypes.c_void_p

    def launch_so(self) -> None:
        """
        Launch the solver using the shared object library.
        """
        n_template_file = len(self.input.template_file)
        m_template_file = self.input.surf_template_width_for_fortran
        n_bulk_file = len(self.input.bulk_file)
        m_bulk_file = self.input.bulk_out_width_for_fortran

        # NOTE: The "20480" is related to the following directive in surf_so.f90.
        # character(c_char), intent(inout) :: surf_out(20480)
        emp_str = " " * 20480
        self.output.surf_output = np.array([emp_str.encode()])
        self.lib.surf_so(
            ctypes.byref(ctypes.c_int(n_template_file)),
            ctypes.byref(ctypes.c_int(m_template_file)),
            self.input.template_file,
            ctypes.byref(ctypes.c_int(n_bulk_file)),
            ctypes.byref(ctypes.c_int(m_bulk_file)),
            self.input.bulk_file,
            self.output.surf_output,
        )
        self.output.surf_output = self.output.surf_output[0].decode().splitlines()

    def _run_by_subprocess(self, command: List[str]) -> None:
        """
        Run the solver using a subprocess.

        Parameters
        ----------
        command : List[str]
            Command to run the solver.
        """
        with open("stdout", "w") as fi:
            subprocess.run(
                command,
                stdout=fi,
                stderr=subprocess.STDOUT,
                check=True,
            )

    def run(self, nprocs: int = 1, nthreads: int = 1) -> None:
        """
        Run the solver.

        Parameters
        ----------
        nprocs : int, optional
            Number of processes.
        nthreads : int, optional
            Number of threads.
        """
        if self.isLogmode:
            time_sta = time.perf_counter()

        if self.run_scheme == "connect_so":
            self.launch_so()
        elif self.run_scheme == "subprocess":
            self._run_by_subprocess([str(self.path_to_solver)])

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["launch_STR"] += time_end - time_sta
