Installation of odatse-STR
================================================================

Prerequisites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Python3 (>=3.6.8)

  - The following Python packages are required.

    - tomli >= 1.2
    - numpy >= 1.14

  - ODAT-SE version 3.0 and later

  - sim-trhepd-rheed version 1.0.2 and later


How to download and install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install ODAT-SE

   - From source files:

     Download source files of ODAT-SE from the repository as follows:

     .. code-block:: bash

	$ git clone -b update https://github.com/issp-center-dev/ODAT-SE.git

     Install ODAT-SE using ``pip`` command:

     .. code-block:: bash

	$ cd ODAT-SE
	$ python3 -m pip install .

     You may add ``--user`` option to install ODAT-SE locally (in ``$HOME/.local``).

     If you run the following command instead, optional packages will also be installed at the same time.

     .. code-block:: bash

	$ python3 -m pip install .[all]

2. Install sim-trhepd-rheed

   - Download the source package from the official site:

     .. code-block:: bash

	$ wget -O sim-trhepd-rheed-1.0.2.tar.gz https://github.com/sim-trhepd-rheed/sim-trhepd-rheed/archive/refs/tags/v1.0.2.tar.gz

   - Unpack the source package, and compile the source. Edit Makefile in sim-trhepd-rheed/src as needed.

     .. code-block:: bash

	$ tar xvfz sim-trhepd-rheed-1.0.2.tar.gz
	$ cd sim-trhepd-rheed-1.0.2/src
	$ make

     The executable files ``bulk.exe``, ``surf.exe``, ``potcalc.exe``, and ``xyz.exe`` will be generated.
     Put ``bulk.exe`` and ``surf.exe`` in a directory listed in the PATH environment variable, or specify the paths to these commands at run time.
     
3. Install odatse-STR

   - From source files:

     The source files of odatse-STR are available from the GitHub repository. After obtaining the source files, install odatse-STR using ``pip`` command as follows:

     .. code-block:: bash

	$ git clone https://github.com/2DMAT/odatse-STR.git
	$ cd odatse-STR
	$ python3 -m pip install .

     You may add ``--user`` option to install the package locally (in ``$HOME/.local``).

     Then, the library of odatse-STR and the command ``odatse-STR`` wil be installed.


How to run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In ODAT-SE, the analysis is done by using a predefined optimization algorithm and a direct problem solver.
There are two ways to do analyses of TRHEPD:

1. Use odatse-STR program included in this package to perform analyses.
   The users prepare an input parameter file in TOML format, and run command with it.
   The type of the inverse problem algorithms can be chosen by the parameter.

2. Write a program for the analysis with odatse-STR library and ODAT-SE framework.
   The type of the inverse problem algorithms can be chosen by importing the appropriate module.
   A flexible use would be possible, for example, to include data generation within the program.
   
The types of parameters and the instruction to use the library will be given in the subsequent sections.


How to uninstall
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In order to uninstall odatse-STR and ODAT-SE modules, type the following commands:

.. code-block:: bash

   $ python3 -m pip uninstall odatse-STR ODAT-SE
