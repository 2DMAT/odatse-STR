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

import itertools
import os
import sys
import time
import ctypes
import shutil

import numpy as np

import odatse
from odatse import exception, mpi
from .input import Input
from .output import Output
from .parameter import parse_solver_info
from .util import Workdir, set_solver_path, run_by_subprocess

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

        self.info = parse_solver_info(**info.solver)

        self.run_scheme = self.info.run_scheme
        if self.run_scheme == "connect_so":
            self.path_to_solver_lib = self.root_dir / Path(self.info.config.surface_exec_file).expanduser()
            self.load_so()
        elif self.run_scheme == "subprocess":
            # path to surf.exe
            self.path_to_solver = set_solver_path(self.info.config.surface_exec_file, self.root_dir)

        self.set_detail_timer(self.info.enable_detailed_timer)

        self.input = Input(self.info, self.root_dir, self.isLogmode, self.detail_timer)
        self.output = Output(self.info, self.isLogmode, self.detail_timer)

    # def __del__(self):
    #     self._show_detail_timer()

    def _show_detail_timer(self):
        if not self.isLogmode:
            return

        msec = 1.0e-3
        if self.mpisize > 1:
            data = self.mpicomm.allgather(self.detail_timer)
            if self.mpirank == 0:
                for k in self.detail_timer.keys():
                    vs = [v[k] for v in data]
                    print("{:25s} = {:12.6f} {:12.6f} [msec]".format(k, np.mean(vs)/msec, np.var(vs)/msec))
        else:
            for k, v in self.detail_timer.items():
                print("{:25s} = {:12.6f} [msec]".format(k, v/msec))

    def set_detail_timer(self, is_enabled) -> None:
        """
        Set the detail timer for logging mode.
        """
        if is_enabled:
            self.isLogmode = True
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
            self.isLogmode = False
            self.detail_timer = {}

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

        if self.run_scheme == "connect_so" and self.info.generate_rocking_curve == False:
            self.input.generate(x)
            self.run(nprocs, nthreads)
            result = self.output.get_results(x)

        else:
            work_dir = "Log{:08d}_{:08d}".format(*args)
            with Workdir(work_dir, remove=self.info.remove_work_dir, use_tmpdir=self.info.use_tmpdir):
                if self.run_scheme == "connect_so":
                    pass
                else:
                    shutil.copy(os.path.join(self.root_dir, self.info.config.bulk_output_file), ".")
                self.input.generate(x)
                self.run(nprocs, nthreads)
                result = self.output.get_results(x)
        return result

    def load_so(self) -> None:
        """
        Load the shared object library for the solver.
        """
        #self.lib = np.ctypeslib.load_library("surf.so", os.path.dirname(__file__))
        self.lib = np.ctypeslib.load_library(self.path_to_solver_lib.name, self.path_to_solver_lib.parent)
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
            run_by_subprocess([str(self.path_to_solver)])

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["launch_STR"] += time_end - time_sta
