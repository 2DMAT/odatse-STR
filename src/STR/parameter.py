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

from typing import Tuple, List, Dict, Union, Optional, Annotated, Literal, Set
from typing_extensions import Self
from annotated_types import Len
from pydantic import BaseModel, PositiveInt, ValidationError, Field, field_validator, model_validator, FilePath, conlist, PositiveFloat, NonNegativeInt
from numbers import Number

from pathlib import Path


class SolverConfig(BaseModel):
    """
    Parameters for configuration of the STR solver

    Attributes
    ----------
    surface_exec_file : str
        Path to the sim-trhepd-rheed executable file.
    surface_input_file : str
        Name of the sim-trhepd-rheed input file.
    surface_template_file : str
        Name of the sim-trhepd-rheed template file.
    bulk_output_file : str
        Name of the bulk output file of sim-trhepd-rheed.
    surface_output_file : str
        Name of the surf output file of sim-trhepd-rheed.
    calculated_first_line : int
        The line number of the first line of the calculated data.
    calculated_last_line : int
        The line number of the last line of the calculated data.
    calculated_info_line : int
        The number of lines of info field in the cauclated data.
    cal_number: int or List[int]
        The column number(s) to be considered in the calculated data.
    """
    surface_exec_file: str = "surf.exe"
    surface_input_file: str = "surf.txt"
    surface_template_file: str = "template.txt"
    bulk_output_file: str = "bulkP.b"
    surface_output_file: str = "surf-bulkP.s"
    calculated_first_line: NonNegativeInt = Field(default=5)
    calculated_last_line: Optional[NonNegativeInt] = None
    calculated_info_line: int = Field(default=2)
    cal_number: Union[int,List[int]] # = Field(min_length=1)

class SolverPost(BaseModel):
    """
    Parameters for post processes of the STR solver

    Attributes
    ----------
    normalization : string literal
        Type of normalization.
    weight_type : string literal
        Type of weight.
    spot_weight : List[float]
        Weighth values.
    Rfactor_type : string literal
        Type of the R-factor.
    omega : float
        Convolution parameter.
    remove_work_dir: bool
        Flag to remove the working directory after execution.
    """
    normalization: Literal["TOTAL", "MANY_BEAM", "MAX"]
    weight_type: Optional[Literal["calc", "manual"]] = None
    spot_weight: Optional[List[float]] = None
    Rfactor_type: Literal["A", "A2", "B"] = "A"
    omega: PositiveFloat = 0.5
    remove_work_dir: bool = False

    @field_validator("normalization")
    def check_obsolete_normalization(cls, v):
        """Check obsolete parameter values."""
        if v == "MAX":
            raise ValueError("normalization=MAX is obsolete")
        return v

class SolverParam(BaseModel):
    """
    Parameters for input files of the STR solver

    Attributes
    ----------
    string_list : List[str]
        List of keywords to be replaced in the template.
    """
    string_list: List[str]

class SolverReference(BaseModel):
    """
    Parameters for reference data of the STR solver

    Attributes
    ----------
    path : str
        Path to the reference data file.
    reference_first_line : int
        The line number of the first line in the reference file.
    reference_last_line: int
        The line number of the last line in the reference file.
    exp_number: int of List[int]
        The column number(s) to be considered in the reference file.
    """
    path: str = "experiment.txt"
    reference_first_line: NonNegativeInt = Field(default=1)
    reference_last_line: Optional[NonNegativeInt] = None
    exp_number: Union[int,List[int]] # = Field(min_length=1)

class SolverInfo(BaseModel):
    """
    Parameters for the STR solver

    Attributes
    ----------
    dimension : int
        Number of variables.
    run_scheme : string literal
        Choice of schemes in executing external solver programs.
    generate_rocking_curve : bool
        Flag to generate theh rocking curve during the calculations.
    config : SolverConfig
        Configuration for the solver.
    post : SolverPost
        Parameters for the post processes.
    param : SolverParam
        Parameters for the solver.
    reference : SolverReference
        Parameters for the reference data.
    """
    dimension: Optional[int] = None
    run_scheme: Literal["subprocess", "connect_so"] = "subprocess"
    generate_rocking_curve: bool = False
    config: SolverConfig
    post: SolverPost
    param: SolverParam
    reference: SolverReference

    @model_validator(mode="after")
    def check_dimension(self) ->Self:
        """Check length of string_list."""
        if self.dimension is not None and len(self.param.string_list) != self.dimension:
            raise ValueError("length of param.string_list does not match with dimension")
        return self

    @model_validator(mode="after")
    def check_normalization(self) -> Self:
        """Check consistency among normalization, weight_type, and spot_weight parameters."""
        if self.post.normalization == "MANY_BEAM":
            if self.post.weight_type is None:
                raise ValueError("weight_type must be set when normalization is MANY_BEAM")
            elif self.post.weight_type == "manual":
                if self.post.spot_weight is None:
                    raise ValueError("spot_weight must be set when weight_type is manual")
            elif self.post.weight_type == "calc":
                if self.post.spot_weight is not None:
                    print("spot_weight is ignored when weight_type is calc")
                    self.post.spot_weight = None
            else:
                raise ValueError("unknown weight_type {}".format(self.post.weight_type))
            if not self.post.Rfactor_type in ["A", "A2"]:
                raise ValueError("Rfactor_type must be A or A2 when normalization is MANY_BEAM")
        elif self.post.normalization == "TOTAL":
            if self.post.weight_type is not None:
                print("weight_type is ignored when normalization is TOTAL")
                self.post.weight_type = None
            if self.post.spot_weight is not None:
                print("spot_weight is ignored when normalization is TOTAL")
                self.post.spot_weight = [1.0]
        else:
            pass
        return self

    @model_validator(mode="after")
    def check_field_lengths(self) -> Self:
        """Check lengths of cal_number and exp_number, consistency with normalization and weights."""
        if isinstance(self.config.cal_number, int):
            self.config.cal_number = [self.config.cal_number]
        if isinstance(self.reference.exp_number, int):
            self.reference.exp_number = [self.reference.exp_number]
        if len(self.config.cal_number) != len(self.reference.exp_number):
            raise ValueError("lenghts of config.cal_number and reference.exp_number differ")
        if self.post.normalization == "MANY_BEAM" and self.post.weight_type == "manual":
            if len(self.config.cal_number) != len(self.post.spot_weight):
                raise ValueError("lengths of config.cal_number and post.spot_weight differ")
            if len(self.reference.exp_number) != len(self.post.spot_weight):
                raise ValueError("lengths of reference.exp_number and post.spot_weight differ")
        elif self.post.normalization == "TOTAL":
            if len(self.config.cal_number) != 1:
                raise ValueError("length of config.cal_number must be 1 when normalization is TOTAL")
            if len(self.reference.exp_number) != 1:
                raise ValueError("length of reference.exp_number must be 1 when normalization is TOTAL")
        return self


if __name__ == "__main__":
    import tomli
    from devtools import pprint

    input_data = """
[solver]
  generate_rocking_curve = true
  run_scheme = "subprocess"
  #dimension = 2
[solver.config]
  surface_exec_file = "surf.exe"
  surface_input_file = "surf.txt"
  bulk_output_file = "bulkP.b"
  surface_output_file = "surf-bulkP.s"
  calculated_first_line = 5
  calculated_info_line = 2
  cal_number = 2 #[2,3]
[solver.post]
  Rfactor_type = "A"
  normalization = "MANY_BEAM"
  #weight_type = "manual"
  weight_type = "calc"
  spot_weight = [1] #[1,3]
  omega = 0.5
  remove_work_dir = false
[solver.param]
  string_list = ["value_01", "value_02"]
[solver.reference]
  path = "experiment.txt"
  reference_first_line = 1
  reference_last_line = 1
  exp_number = 3 #[4,5]
"""

    params = tomli.loads(input_data)
    si = SolverInfo(**params["solver"])

    pprint(si)
