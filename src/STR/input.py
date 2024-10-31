import os
import shutil
import numpy as np

# for type hints
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mpi4py import MPI

from odatse import exception, mpi

class Input(object):
    """
    A class to handle input data and configurations for the simulation.

    Attributes:
        mpicomm (Optional[MPI.Comm]): MPI communicator.
        mpisize (int): Size of the MPI communicator.
        mpirank (int): Rank of the MPI communicator.
        root_dir (Path): Root directory for the simulation.
        output_dir (Path): Output directory for the simulation.
        dimension (int): Dimension of the simulation.
        run_scheme (str): Scheme to run the simulation.
        generate_rocking_curve (bool): Flag to generate rocking curve.
        string_list (List[str]): List of strings for the simulation.
        bulk_output_file (Path): Path to the bulk output file.
        surface_input_file (Path): Path to the surface input file.
        surface_template_file (Path): Path to the surface template file.
        template_file_origin (List[str]): Original template file content.
    """

    def __init__(self, info, isLogmode, detail_timer):
        """
        Initializes the Input class with the given parameters.

        Args:
            info: Information object containing base and solver configurations.
            isLogmode (bool): Flag to enable logging mode.
            detail_timer: Timer object for detailed timing.
        """
        self.mpicomm = mpi.comm()
        self.mpisize = mpi.size()
        self.mpirank = mpi.rank()

        self.isLogmode = isLogmode
        self.detail_timer = detail_timer

        self.root_dir = info.base["root_dir"]
        self.output_dir = info.base["output_dir"]

        if "dimension" in info.solver:
            self.dimension = info.solver["dimension"]
        else:
            self.dimension = info.base["dimension"]

        # read info
        info_s = info.solver
        self.run_scheme = info_s["run_scheme"]
        self.generate_rocking_curve = info_s.get("generate_rocking_curve", False)

        # NOTE:
        # surf_template_width_for_fortran: Number of strings per line of template.txt data for surf.so.
        # bulk_out_width_for_fortran: Number of strings per line of bulkP.txt data for surf.so.
        if self.run_scheme == "connect_so":
            self.surf_template_width_for_fortran = 128
            self.bulk_out_width_for_fortran = 1024

        info_param = info_s.get("param", {})
        v = info_param.setdefault("string_list", ["value_01", "value_02"])
        if len(v) != self.dimension:
            raise exception.InputError(
                f"ERROR: len(string_list) != dimension ({len(v)} != {self.dimension})"
            )
        self.string_list = v

        info_config = info_s.get("config", {})
        self.surface_input_file = Path(
            info_config.get("surface_input_file", "surf.txt")
        )

        filename = info_config.get("surface_template_file", "template.txt")
        filename = Path(filename).expanduser().resolve()
        self.surface_template_file = self.root_dir / filename
        if not self.surface_template_file.exists():
            raise exception.InputError(
                f"ERROR: surface_template_file ({self.surface_template_file}) does not exist"
            )

        if self.mpirank == 0:
            self._check_template()
            temp_origin = self.load_surface_template_file(filename)
        else:
            temp_origin = None
        if self.mpisize > 1:
            self.template_file_origin = self.mpicomm.bcast(temp_origin, root=0)
        else:
            self.template_file_origin = temp_origin

        if self.run_scheme == "connect_so":
            filename = info_config.get("bulk_output_file", "bulkP.txt")
            filename = Path(filename).expanduser().resolve()
            self.bulk_output_file = self.root_dir / filename
            if not self.bulk_output_file.exists():
                raise exception.InputError(
                    f"ERROR: bulk_output_file ({self.bulk_output_file}) does not exist"
                )

            if self.mpirank == 0:
                bulk_f = self.load_bulk_output_file(filename)
            else:
                bulk_f = None
            if self.mpisize > 1:
                self.bulk_file = self.mpicomm.bcast(bulk_f, root=0)
            else:
                self.bulk_file = bulk_f
        else:
            filename = info_config.get("bulk_output_file", "bulkP.b")
            filename = Path(filename).expanduser().resolve()
            self.bulk_output_file = self.root_dir / filename
            if not self.bulk_output_file.exists():
                raise exception.InputError(
                    f"ERROR: bulk_output_file ({self.bulk_output_file}) does not exist"
                )

    def load_surface_template_file(self, filename):
        """
        Loads the surface template file.

        Args:
            filename (str): The name of the surface template file.

        Returns:
            List[str]: The content of the surface template file.
        """
        template_file = []
        with open(self.surface_template_file) as f:
            for line in f:
                template_file.append(line)
        return template_file

    def load_bulk_output_file(self, filename):
        """
        Loads the bulk output file.

        Args:
            filename (str): The name of the bulk output file.

        Returns:
            np.ndarray: The content of the bulk output file as a numpy array.
        """
        bulk_file = []
        with open(self.bulk_output_file) as f:
            for line in f:
                line = line.replace("\t", " ").replace("\n", " ")
                line = line.encode().ljust(self.bulk_out_width_for_fortran)
                bulk_file.append(line)
        bulk_f = np.array(bulk_file)
        return bulk_f

    def prepare(self, x: np.ndarray, args):
        """
        Prepares the input data for the simulation.

        Args:
            x (np.ndarray): The input data array.
            args: Additional arguments for preparation.

        Returns:
            Tuple[List[str], str]: The fitted x list and folder name.
        """
        if self.isLogmode:
            time_sta = time.perf_counter()

        # x_list = message.x
        # step = message.step
        # iset = message.set
        x_list = x
        step, iset = args

        dimension = self.dimension
        string_list = self.string_list
        bulk_output_file = self.bulk_output_file
        solver_input_file = self.surface_input_file
        fitted_x_list = []
        for index in range(dimension):
            fitted_value = " " if x_list[index] >= 0 else ""
            fitted_value += format(x_list[index], ".8f")
            fitted_value = fitted_value[: len(string_list[index])]
            fitted_x_list.append(fitted_value)

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["make_surf_input"] += time_end - time_sta

        if self.isLogmode:
            time_sta = time.perf_counter()

        folder_name = "."
        if self.generate_rocking_curve:
            folder_name = self._pre_bulk(step, bulk_output_file, iset)
        else:
            if self.run_scheme == "connect_so":
                folder_name = "."

            elif self.run_scheme == "subprocess":
                # make workdir and copy bulk output file
                folder_name = self._pre_bulk(step, bulk_output_file, iset)

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["prepare_Log-directory"] += time_end - time_sta

        if self.isLogmode:
            time_sta = time.perf_counter()

        self._replace(fitted_x_list, folder_name)

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["make_surf_input"] += time_end - time_sta

        return fitted_x_list, folder_name

    def _pre_bulk(self, Log_number, bulk_output_file, iset):
        """
        Prepares the bulk output file for the simulation.

        Args:
            Log_number (int): The log number for the simulation.
            bulk_output_file (Path): The path to the bulk output file.
            iset: The set identifier.

        Returns:
            str: The folder name for the bulk output file.
        """
        folder_name = "Log{:08d}_{:08d}".format(Log_number, iset)
        os.makedirs(folder_name, exist_ok=True)
        if self.run_scheme == "connect_so":
            pass
        else:  # self.run_scheme == "subprocess":
            shutil.copy(
                bulk_output_file, os.path.join(folder_name, bulk_output_file.name)
            )
        return folder_name

    def _replace(self, fitted_x_list, folder_name):
        """
        Replaces placeholders in the template file with fitted values.

        Args:
            fitted_x_list (List[str]): The list of fitted values.
            folder_name (str): The folder name for the output files.
        """
        template_file = []
        if self.run_scheme == "subprocess":
            file_output = open(
                os.path.join(folder_name, self.surface_input_file), "w"
            )
        for line in self.template_file_origin:
            for index in range(self.dimension):
                if line.find(self.string_list[index]) != -1:
                    line = line.replace(
                        self.string_list[index], fitted_x_list[index]
                    )

            if self.run_scheme == "connect_so":
                line = line.replace("\t", " ").replace("\n", " ")
                line = line.encode().ljust(self.surf_template_width_for_fortran)
                template_file.append(line)

            elif self.run_scheme == "subprocess":
                file_output.write(line)

        if self.run_scheme == "connect_so":
            self.template_file = np.array(template_file)
        elif self.run_scheme == "subprocess":
            file_output.close()

    def _check_template(self) -> None:
        """
        Checks if all placeholders are present in the template file.

        Raises:
            InputError: If any placeholder is missing in the template file.
        """
        found = [False] * self.dimension
        with open(self.surface_template_file, "r") as file_input:
            for line in file_input:
                for index, placeholder in enumerate(self.string_list):
                    if line.find(placeholder) != -1:
                        found[index] = True
        if not np.all(found):
            msg = "ERROR: the following labels do not appear in the template file:"
            for label, f in zip(self.string_list, found):
                if not f:
                    msg += "\n"
                    msg += label
            raise exception.InputError(msg)