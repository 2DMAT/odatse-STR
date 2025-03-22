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

from typing import Dict, List, Tuple
from pathlib import Path

import os
import time
import numpy as np

from odatse import mpi
from .template import Template

# use custom formatter for parameter values to substitute
def formatter(key, value, fmt):
    s = " " if value >= 0 else ""
    s += format(value, ".8f")
    s = s[:len(key)]
    return s


class Input:

    # constant parameters
    surf_template_width_for_fortran = 128
    bulk_out_width_for_fortran = 1024

    def __init__(self, info, root_dir = ".", isLogmode = False, detail_timer = {}):
        self.isLogmode = isLogmode
        self.detail_timer = detail_timer

        format_list = {
            "*": "{:.8f}",
        }

        string_list = info.param.string_list
        base_dir = Path(root_dir) / Path(info.config.path_to_base_dir).expanduser()

        self.tmpl = Template(file=os.path.join(base_dir, info.config.surface_template_file), keywords=string_list, style="custom", formatter=formatter)

        self.run_scheme = info.run_scheme

        self.bulk_output_file = os.path.join(base_dir, info.config.bulk_output_file)
        if self.run_scheme == "connect_so":
            self.bulk_file = self._load_bulk_output_file(self.bulk_output_file)
        else:
            self.bulk_file = None

        self.surface_input_file = Path(info.config.surface_input_file)

    def generate(self, xs: np.ndarray):
        if self.isLogmode:
            time_sta = time.perf_counter()

        if self.run_scheme == "connect_so":
            data = self.tmpl.generate(xs)
            self.template_file = np.array([
                s.strip().encode().ljust(self.surf_template_width_for_fortran)
                for s in data.splitlines()
            ])
        else:
            self.tmpl.generate(xs, output=self.surface_input_file)
            self.template_file = None

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["make_surf_input"] += time_end - time_sta

    def _load_bulk_output_file(self, filename):
        """
        Loads the bulk output file.

        Parameters
        ----------
        filename : str
            The name of the bulk output file.

        Returns
        -------
        np.ndarray
            The content of the bulk output file as a numpy array.
        """
        mpisize = mpi.size()
        mpirank = mpi.rank()
        mpicomm = mpi.comm()

        if mpirank == 0:
            bulk_file = []
            with open(filename) as f:
                for line in f:
                    line = line.replace("\t", " ").replace("\n", " ")
                    line = line.encode().ljust(self.bulk_out_width_for_fortran)
                    bulk_file.append(line)
            bulk_f = np.array(bulk_file)
        else:
            bulk_f = None

        if mpisize > 1:
            self.bulk_file = mpicomm.bcast(bulk_f, root=0)
        else:
            self.bulk_file = bulk_f

        return bulk_f
