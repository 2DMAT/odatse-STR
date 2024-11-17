import os
import sys
import pytest
from pydantic import ValidationError

SOURCE_PATH = os.path.join(os.path.dirname(__file__), '../../src')
sys.path.append(SOURCE_PATH)

def test_parameters():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)
    info = SolverInfo(**params["solver"])

    assert True
    
def test_normalization_obsolete():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "MAX"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)

    with pytest.raises(Exception) as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError
    
def test_dimension():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    dimension = 2
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="length of param.string_list") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError

def test_cal_exp_number():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1,2]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="lenghts of config.cal_number and reference.exp_number differ") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError

def test_many_beam_array_lengths():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1,2]
    [solver.post]
    normalization = "MANY_BEAM"
    weight_type = "manual"
    spot_weight = [1,2,3]
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1,2]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="lengths of config.cal_number and post.spot_weight differ") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError

def test_total_cal_number():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1,2]
    [solver.post]
    normalization = "TOTAL"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1,2]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="length of config.cal_number must be 1") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError

def test_many_beam_no_weight_type():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "MANY_BEAM"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="weight_type must be set") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError
    
def test_many_beam_no_spot_weight():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "MANY_BEAM"
    weight_type = "manual"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="spot_weight must be set") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError
    
def test_many_beam_Rfactor_type():
    import tomli
    from STR.parameter import SolverInfo

    input_data = """
    [solver]
    [solver.config]
    cal_number = [1]
    [solver.post]
    normalization = "MANY_BEAM"
    weight_type = "calc"
    Rfactor_type = "B"
    [solver.param]
    string_list = ["Sx", "Sy", "Sz"]
    [solver.reference]
    exp_number = [1]
    """

    params = tomli.loads(input_data)

    with pytest.raises(ValidationError, match="Rfactor_type must be A or A2") as excinfo:
        info = SolverInfo(**params["solver"])

    assert excinfo.type is ValidationError
