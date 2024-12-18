Analyses by user programs
================================================================

In this tutorial, we will write a user program using odatse-STR module and perform analyese. As an example, we adopt Nelder-Mead method for the inverse problem algorithm.


Location of the sample files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The sample files are located in ``sample/single_beam/user_program``.
The following files are stored in the folder.

- ``simple.py``

  Source file of the main program. This program reads ``input.toml`` for the parameters.

- ``input.toml``

  Input file of the main program.

- ``experiment.txt``, ``template.txt``

  Reference file to proceed with calculations in the main program.

- ``ref.txt``

  A file containing the answers you want to seek in this tutorial.

- ``simple2.py``

  Another version of source file of the main program. The parameters are embedded in the program as a dict.

- ``prepare.sh`` , ``do.sh``

  Script prepared for doing all calculation of this tutorial

The following sections describe these files and then show the actual calculation results.


Description of main program
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``simple.py`` is a simple program for the analyses using odatse-STR module.
The entire source file is shown as follows:

.. code-block:: python

    import numpy as np

    import odatse
    import odatse.algorithm.min_search
    from odatse.extra.STR import Solver

    info = odatse.Info.from_file("input.toml")

    solver = Solver(info)
    runner = odatse.Runner(solver, info)
    alg = odatse.algorithm.min_search.Algorithm(info, runner)
    alg.main()

At the beginning of the program, the required modules are imported as listed below.

- ``odatse`` for the main module of ODAT-SE.

- ``odatse.algorithm.min_search`` for the module of the inverse problem algorithm used in this tutorial.

- ``odatse.extra.STR`` for the direct problem solver module.

Next, the instances of the classes are created.

- ``odatse.Info`` class

  This class is for storing the parameters. It is created by calling a class method ``from_file`` with a path to TOML file as an argument.

- ``odatse.extra.STR.Solver`` class

  This class is for the direct problem solver of the odatse-STR module. It is created by passing an instance of Info class.

- ``odatse.Runner`` class

  This class is for connecting the direct problem solver and the inverse problem algorithm. It is created by passing an instance of Solver class and an instance of Info class.

- ``odatse.algorithm.min_search.Algorithm`` class

  This class is for the inverse problem algorithm. In this tutorial, we use ``min_search`` module that implements the optimization by Nelder-Mead method. It is created by passing an instance of Runner class.

After creating the instances of Solver, Runner, and Algorithm in this order, we invoke ``main()`` method of the Algorithm class to start analyses.

In the above program, the input parameters are read from a file in TOML format. It is also possible to take the parameters in the form of dictionary.
``simple2.py`` is anther version of the main program in which the parameters are embedded in the program. The entire source file is shown below:

.. code-block:: python

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

An instance of Info class is created by passing a set of parameters in a dict form.
It is also possible to generate the parameters within the program before passing to the class.


Input files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The input file ``input.toml`` for the main program is the same as that used in the previous tutorial for Nelder-Mead method.
Except, ``algorithm.name`` parameter for specifying the algorithm type should be ignored.

``template.txt`` and ``experiment.txt`` are the same as those in the previous tutorials.


Calculation execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, move to the folder where the sample files are located. (We assume that you are directly under the directory where you downloaded this software.)

.. code-block::

   $ cd sample/single_beam/user_program

Copy ``bulk.exe`` and ``surf.exe``.

.. code-block::

   $ cp ../../sim-trhepd-rheed/src/bulk.exe .
   $ cp ../../sim-trhepd-rheed/src/surf.exe .

Run ``bulk.exe`` to produce ``bulkP.b``.

.. code-block::

   $ ./bulk.exe

Then, run the main program. The computation time will take only a few seconds on a normal PC.

.. code-block::

   $ python3 simple.py | tee log.txt

The standard output will look as follows.

.. code-block::

    name            : minsearch
    label_list      : ['z1', 'z2', 'z3']
    param.min_list  : [0.0, 0.0, 0.0]
    param.max_list  : [10.0, 10.0, 10.0]
    param.initial_list: [5.25, 4.25, 3.5]
    eval: x=[5.25 4.25 3.5 ], fun=0.015199252435883206
    eval: x=[5.22916667 4.3125     3.64583333], fun=0.013702918645281299
    eval: x=[5.22569444 4.40625    3.54513889], fun=0.01263527811899235
    eval: x=[5.17997685 4.34895833 3.5943287 ], fun=0.006001659635528168
    eval: x=[5.17997685 4.34895833 3.5943287 ], fun=0.006001659635528168
    eval: x=[5.22066294 4.33260995 3.60408629], fun=0.005145496928704404
    eval: x=[5.22066294 4.33260995 3.60408629], fun=0.005145496928704404
    eval: x=[5.2185245  4.32627234 3.56743818], fun=0.0032531465329236025
    eval: x=[5.19953437 4.34549482 3.5863457 ], fun=0.0027579225484420356
    eval: x=[5.21549776 4.35100199 3.57476018], fun=0.002464573036316852
    ...

``x=`` are the candidate parameters at each step, and ``fun=`` is the R-factor value at that point.
The results at each step are also written in the folder ``output/LogXXXX_YYYY`` (where XXXX and YYYY are the step counts).
The final estimated parameters will be written to ``output/res.dat``. 
In the current case, the following result will be obtained:

.. code-block::

    z1 = 5.230524973874179
    z2 = 4.370622919269477
    z3 = 3.5961444501081647

You can see that we will get the same values as the correct answer data in ``ref.txt``.

Note that ``do.sh`` is available as a script for batch calculation.

