import os
import numpy as np

# for type hints
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mpi4py import MPI

from odatse import exception, mpi
from . import lib_make_convolution

class Output(object):
    """
    Output manager.
    """

    mpicomm: Optional["MPI.Comm"]
    mpisize: int
    mpirank: int

    run_scheme: str
    generate_rocking_curve: bool
    dimension: int
    normalization: str
    weight_type: Optional[str]
    spot_weight: List
    Rfactor_type: str
    omega: float
    remove_work_dir: bool
    string_list: List[str]
    reference_first_line: int
    reference_last_line: Optional[int]
    reference_path: str
    exp_number: List
    I_reference_normalized_l: np.ndarray
    surface_output_file: str
    calculated_first_line: int
    calculated_last_line: int
    calculated_info_line: int
    cal_number: List

    def __init__(self, info, isLogmode, detail_timer):
        self.mpicomm = mpi.comm()
        self.mpisize = mpi.size()
        self.mpirank = mpi.rank()

        self.isLogmode = isLogmode
        self.detail_timer = detail_timer

        if "dimension" in info.solver:
            self.dimension = info.solver["dimension"]
        else:
            self.dimension = info.base["dimension"]

        info_s = info.solver
        self.run_scheme = info_s["run_scheme"]

        # If self.run_scheme == "connect_so",
        # the contents of surface_output_file are retailned in self.surf_output.
        self.surf_output = np.array([])
        self.generate_rocking_curve = info_s.get("generate_rocking_curve", False)

        # solver.post
        info_post = info_s.get("post", {})
        v = info_post.get("normalization", "")
        available_normalization = ["TOTAL", "MANY_BEAM"]
        if v == "MAX":
            raise exception.InputError(
                'ERROR: solver.post.normalization == "MAX" is no longer available'
            )
        if v not in available_normalization:
            msg = "ERROR: solver.post.normalization must be "
            msg += "MANY_BEAM or TOTAL"
            raise exception.InputError(msg)
        self.normalization = v

        v = info_post.get("weight_type", None)
        available_weight_type = ["calc", "manual"]
        if self.normalization == "MANY_BEAM":
            if v is None:
                msg = 'ERROR: If solver.post.normalization = "MANY_BEAM", '
                msg += '"weight_type" must be set in [solver.post].'
                raise exception.InputError(msg)
            elif v not in available_weight_type:
                msg = "ERROR: solver.post.weight_type must be "
                msg += "calc or manual"
                raise exception.InputError(msg)
        else:
            if v is not None:
                if self.mpirank == 0:
                    msg = 'NOTICE: If solver.post.normalization = "MANY_BEAM" is not set, '
                    msg += '"solver.post.weight_type" is NOT considered in the calculation.'
                    print(msg)
                self.weight_type = None
        self.weight_type = v

        v = info_post.get("spot_weight", [])
        if self.normalization == "MANY_BEAM" and self.weight_type == "manual":
            if v == []:
                msg = 'ERROR: With solver.post.normalization="MANY_BEAM" and '
                msg += 'solver.post.weight_type=="manual", the "spot_weight" option '
                msg += "must be set in [solver.post]."
                raise exception.InputError(msg)
            self.spot_weight = np.array(v) / sum(v)
        else:
            if v != []:
                if self.mpirank == 0:
                    msg = 'NOTICE: With the specified "solver.post.normalization" option, '
                    msg += 'the "spot_weight" you specify in the toml file is ignored, '
                    msg += "since the spot_weight is automatically calculated within the program."
                    print(msg)
            if self.normalization == "TOTAL":
                self.spot_weight = np.array([1])

        v = info_post.get("Rfactor_type", "A")
        if v not in ["A", "B", "A2"]:
            raise exception.InputError("ERROR: solver.post.Rfactor_type must be A, A2 or B")
        if self.normalization == "MANY_BEAM":
            if (v != "A") and (v != "A2"):
                msg = 'With solver.post.normalization="MANY_BEAM", '
                msg += 'only solver.post.Rfactor_type="A" or "A2" is valid.'
                raise exception.InputError(msg)
        self.Rfactor_type = v

        v = info_post.get("omega", 0.5)
        if v <= 0.0:
            raise exception.InputError("ERROR: omega should be positive")
        self.omega = v

        self.remove_work_dir = info_post.get("remove_work_dir", False)

        # solver.param
        info_param = info_s.get("param", {})
        v = info_param.setdefault("string_list", ["value_01", "value_02"])
        if len(v) != self.dimension:
            raise exception.InputError(
                f"ERROR: len(string_list) != dimension ({len(v)} != {self.dimension})"
            )
        self.string_list = v

        # solver.reference
        info_ref = info_s.get("reference", {})
        v = info_ref.setdefault("reference_first_line", 1)
        if not (isinstance(v, int) and v >= 0):
            raise exception.InputError(
                "ERROR: reference_first_line should be non-negative integer"
            )
        firstline = v

        # None is dummy value
        # If "reference_last_line" is not specified in the toml file,
        # the last line of the reference file is used for the R-factor calculation.
        v = info_ref.setdefault("reference_last_line", None)
        if v is None:
            reference_are_read_to_final_line = True
        else:
            reference_are_read_to_final_line = False
            if not (isinstance(v, int) and v >= firstline):
                raise exception.InputError(
                    "ERROR: reference_last_line < reference_first_line"
                )
        lastline = v

        reference_path = info_ref.get("path", "experiment.txt")
        data_experiment = self.read_experiment(
            reference_path, firstline, lastline, reference_are_read_to_final_line
        )
        self.angle_number_experiment = data_experiment.shape[0]
        self.beam_number_exp_raw = data_experiment.shape[1]

        v = info_ref.get("exp_number", [])
        if isinstance(v, int):
            v = [v]
        if len(v) == 0:
            raise exception.InputError("ERROR: You have to set the 'solver.reference.exp_number'.")

        if not isinstance(v, list):
            raise exception.InputError("ERROR: 'solver.reference.exp_number' must be a list type.")

        if max(v) > self.beam_number_exp_raw:
            raise exception.InputError("ERROR: The 'solver.reference.exp_number' setting is wrong.")

        if self.normalization == "MANY_BEAM" and self.weight_type == "manual":
            if len(v) != len(self.spot_weight):
                raise exception.InputError(
                    "ERROR:len('solver.reference.exp_number') and len('solver.post.spot_weight') do not match."
                )

        if self.normalization == "TOTAL" and len(v) != 1:
            msg = 'When solver.post.normalization=="TOTAL" is specified, '
            msg += "only one beam data can be specified with "
            msg += '"solver.reference.exp_number" option.'
            raise exception.InputError(msg)

        self.exp_number = v

        # Normalization of reference data

        if self.normalization == "TOTAL":
            data = data_experiment[:, [-1]]
            norm = np.sum(data)
            data_normalized = data / norm
            self.I_reference_normalized_l = data_normalized.transpose()

        elif self.normalization == "MANY_BEAM":
            data = data_experiment[:,self.exp_number]
            norm = np.sum(data, axis=0)
            data_normalized = data / norm
            self.I_reference_normalized_l = data_normalized.transpose()

        else:
            raise ValueError("normalization must be MANY_BEAM or TOTAL")

        # solver.config
        info_config = info_s.get("config", {})
        self.surface_output_file = info_config.get(
            "surface_output_file", "surf-bulkP.s"
        )

        v = info_config.get("calculated_first_line", 5)
        if not (isinstance(v, int) and v >= 0):
            raise exception.InputError(
                "ERROR: solver.config.calculated_first_line should be non-negative integer"
            )
        self.calculated_first_line = v

        v = info_config.get(
            "calculated_last_line",
            self.calculated_first_line + self.angle_number_experiment - 1,
        )
        if not (isinstance(v, int) and v >= 0):
            raise exception.InputError(
                "ERROR: solver.config.calculated_last_line should be non-negative integer"
            )
        self.calculated_last_line = v

        # Number of lines in the computation file
        # used for R-factor calculations.
        self.calculated_nlines = (
            self.calculated_last_line - self.calculated_first_line + 1
        )

        if self.angle_number_experiment != self.calculated_nlines:
            raise exception.InputError(
                "ERROR: The number of glancing angles in the calculation data does not match the number of glancing angles in the experimental data."
            )

        # Variable indicating whether the warning
        # "self.calculated_nlines does not match
        #  the number of glancing angles in the calculated file"
        # is displayed.
        self.isWarning_calcnline = False

        v = info_config.get("calculated_info_line", 2)
        if not (isinstance(v, int) and v >= 0):
            raise exception.InputError(
                "ERROR: solver.config.calculated_info_line should be non-negative integer"
            )
        self.calculated_info_line = v

        v = info_config.get("cal_number", [])
        if isinstance(v, int):
            v = [v]
        if len(v) == 0:
            raise exception.InputError("ERROR: You have to set the 'solver.config.cal_number'.")

        if not isinstance(v, list):
            raise exception.InputError("ERROR: 'solver.config.cal_number' must be a list type.")

        if self.normalization == "MANY_BEAM" and self.weight_type == "manual":
            if len(self.spot_weight) != len(v):
                raise exception.InputError(
                    "len('solver.config.cal_number') and len('solver.post.spot_weight') do not match."
                )
        if self.normalization == "TOTAL" and len(v) != 1:
            msg = 'When solver.post.normalization=="TOTAL" is specified, '
            msg += "only one beam data can be specified with "
            msg += '"solver.config.cal_number" option.'
            raise exception.InputError(msg)
        self.cal_number = v

    def read_experiment(self, ref_path, first, last, read_to_final_line):
        # Read experiment data
        if self.mpirank == 0:
            assert first > 0

            if read_to_final_line:
                nlines = None
            else:
                nlines = last - first + 1

            data_e = np.loadtxt(ref_path, skiprows=first-1, max_rows=nlines)

        else:
            data_e = None
        if self.mpisize > 1:
            data_exp = self.mpicomm.bcast(data_e, root=0)
        else:
            data_exp = data_e
        return data_exp

    def prepare(self, fitted_x_list):
        self.fitted_x_list = fitted_x_list

    def get_results(self, work_dir) -> float:
        """
        Get Rfactor obtained by the solver program.
        Returns
        -------
        """
        # Calculate Rfactor and Output numerical results
        cwd = os.getcwd()
        os.chdir(work_dir)
        Rfactor = self._post(self.fitted_x_list)
        os.chdir(cwd)

        # delete Log-directory
        if self.isLogmode:
            time_sta = time.perf_counter()

        if self.run_scheme == "subprocess":
            if self.remove_work_dir:

                def rmtree_error_handler(function, path, excinfo):
                    print(f"WARNING: Failed to remove a working directory, {path}")

                shutil.rmtree(work_dir, onerror=rmtree_error_handler)

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["delete_Log-directory"] += time_end - time_sta
        return Rfactor

    def _post(self, fitted_x_list):
        I_experiment_normalized_l = self.I_reference_normalized_l

        (
            glancing_angle,
            conv_number_of_g_angle,
            conv_I_calculated_norm_l,
            conv_I_calculated_normalized_l,
        ) = self._calc_I_from_file()

        if self.isLogmode:
            time_sta = time.perf_counter()

        Rfactor = self._calc_Rfactor(
            conv_number_of_g_angle,
            conv_I_calculated_normalized_l,
            I_experiment_normalized_l,
        )
        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["calculate_R-factor"] += time_end - time_sta

        if self.generate_rocking_curve:
            self._generate_rocking_curve(fitted_x_list, glancing_angle, conv_I_calculated_normalized_l, Rfactor)

        return Rfactor

    def _generate_rocking_curve(self, fitted_x_list, glancing_angle, conv_I_calculated_normalized_l, Rfactor):
        # generate RockingCurve_calculated.txt
        dimension = self.dimension
        string_list = self.string_list
        cal_number = self.cal_number
        spot_weight = self.spot_weight
        weight_type = self.weight_type
        Rfactor_type = self.Rfactor_type
        normalization = self.normalization

        if self.isLogmode:
            time_sta = time.perf_counter()

        with open("RockingCurve_calculated.txt", "w") as fp:
            # Write headers
            fp.write("#")
            for index in range(dimension):
                fp.write(
                    "{} = {} ".format(string_list[index], fitted_x_list[index])
                )
            fp.write("\n")
            fp.write("#Rfactor_type = {}\n".format(Rfactor_type))
            fp.write("#normalization = {}\n".format(normalization))
            if weight_type is not None:
                fp.write("#weight_type = {}\n".format(weight_type))
            fp.write("#fx(x) = {}\n".format(Rfactor))
            fp.write("#cal_number = {}\n".format(cal_number))
            fp.write("#spot_weight = {}\n".format(spot_weight))
            fp.write(
                "#NOTICE : Intensities are NOT multiplied by spot_weight.\n"
            )
            fp.write(
                "#The intensity I_(spot) for each spot is normalized as in the following equation.\n"
            )
            fp.write("#sum( I_(spot) ) = 1\n")
            fp.write("#\n")

            label_column = ["glancing_angle"]
            fmt_rc = "%.5f"
            for i in range(len(cal_number)):
                label_column.append(f"cal_number={self.cal_number[i]}")
                fmt_rc += " %.15e"

            for i in range(len(label_column)):
                fp.write(f"# #{i} {label_column[i]}")
                fp.write("\n")
            g_angle_for_rc = np.array([glancing_angle])
            np.savetxt(
                fp,
                np.block([g_angle_for_rc.T, conv_I_calculated_normalized_l.T]),
                fmt=fmt_rc,
            )

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["make_RockingCurve.txt"] += time_end - time_sta

    def _calc_I_from_file(self):
        if self.isLogmode:
            time_sta = time.perf_counter()

        surface_output_file = self.surface_output_file
        calculated_first_line = self.calculated_first_line
        calculated_last_line = self.calculated_last_line
        calculated_info_line = self.calculated_info_line
        calculated_nlines = self.calculated_nlines
        omega = self.omega

        cal_number = self.cal_number

        assert 0 < calculated_nlines

        if self.run_scheme == "connect_so":
            Clines = self.surf_output

        elif self.run_scheme == "subprocess":
            file_input = open(self.surface_output_file, "r")
            Clines = file_input.readlines()
            file_input.close()

        # Reads the number of glancing angles and beams
        line = Clines[calculated_info_line - 1]
        line = line.replace(",", "")
        data = line.split()

        calc_number_of_g_angles_org = int(data[1])
        calc_number_of_beams_org = int(data[2])

        if calc_number_of_g_angles_org != calculated_nlines:
            if self.mpirank == 0 and not self.isWarning_calcnline:
                msg = "WARNING:\n"
                msg += "The number of lines in the calculated file "
                msg += "that you have set up does not match "
                msg += "the number of glancing angles in the calculated file.\n"
                msg += "The number of lines (nline) in the calculated file "
                msg += "used for the R-factor calculation "
                msg += "is determined by the following values\n"
                msg += (
                    'nline = "calculated_last_line" - "calculated_first_line" + 1.'
                )
                print(msg)
                self.isWarning_calcnline = True
        calc_number_of_g_angles = calculated_nlines

        # Define the array for the original calculated data.
        RC_data_org = np.zeros(
            (calc_number_of_g_angles, calc_number_of_beams_org + 1)
        )
        for g_angle_index in range(calc_number_of_g_angles):
            line_index = (calculated_first_line - 1) + g_angle_index
            line = Clines[line_index]
            line = line.replace(",", "")
            data = line.split()
            RC_data_org[g_angle_index, 0] = float(data[0])
            for beam_index in range(calc_number_of_beams_org):
                RC_data_org[g_angle_index, beam_index + 1] = data[beam_index + 1]

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["load_STR_result"] += time_end - time_sta

        if self.isLogmode:
            time_sta = time.perf_counter()
        verbose_mode = False
        # convolution
        data_convolution = lib_make_convolution.calc(
            RC_data_org,
            #calc_number_of_beams_org,
            #calc_number_of_g_angles,
            omega,
            #verbose_mode,
        )

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["convolution"] += time_end - time_sta

        if self.isLogmode:
            time_sta = time.perf_counter()

        angle_number_convolution = data_convolution.shape[0]
        if self.angle_number_experiment != angle_number_convolution:
            raise exception.InputError(
                "ERROR: The number of glancing angles in the calculation data does not match the number of glancing angles in the experimental data."
            )
        glancing_angle = data_convolution[:, 0]

        if self.normalization == "TOTAL":
            data = data_convolution[:, [-1]]
            norm = np.sum(data)
            data_normalized = (data / norm).transpose()

        elif self.normalization == "MANY_BEAM":
            data = data_convolution[:, cal_number]
            norm = np.sum(data, axis=0)
            data_normalized = (data / norm).transpose()

            if self.weight_type == "calc":
                self.spot_weight = (norm / np.sum(norm))**2
            elif self.weight_type == "manual":
                pass
            else:
                raise ValueError("unsupported weight type {}".format(self.weight_type))
        else:
            raise ValueError("unsupported normalization {}".format(self.normalization))

        if self.isLogmode:
            time_end = time.perf_counter()
            self.detail_timer["normalize_calc_I"] += time_end - time_sta

        return (
            glancing_angle,
            angle_number_convolution,
            norm,
            data_normalized,
        )

    def _calc_Rfactor(self, n_g_angle, calc_result, exp_result):
        spot_weight = self.spot_weight
        n_spot = len(spot_weight)

        spot = spot_weight[:n_spot]
        expr = exp_result[:n_spot, :n_g_angle]
        calc = calc_result[:n_spot, :n_g_angle]

        if self.Rfactor_type == "A":
            R = np.sum(spot * np.sum((expr - calc)**2, axis=1))
            R = np.sqrt(R)

        elif self.Rfactor_type == "A2":
            R = np.sum(spot * np.sum((expr - calc)**2, axis=1))

        elif self.Rfactor_type == "B":
            assert(n_spot == 1)

            v_exp = expr
            v_cal = calc

            vd = np.sum((v_exp - v_cal)**2, axis=1)
            ve = np.sum(v_exp**2, axis=1)
            vc = np.sum(v_cal**2, axis=1)
            R = np.sum(vd /(ve + vc))
        else:
            raise ValueError("invalid Rfactor_type {}".format(self.Rfactor_type))

        return R
