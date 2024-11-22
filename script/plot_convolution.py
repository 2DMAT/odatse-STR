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

import numpy as np
import matplotlib.pyplot as plt
import sys

args = sys.argv

input_file = "convolution.txt"
if len(args) >= 2:
    input_file = args[1]

data = np.loadtxt(input_file, unpack=True)
    
plt.plot(data[0], data[1], marker = "$o$", linewidth = 1.0)
plt.xlabel("degree")
plt.ylabel("I")
plt.savefig("plot_convolution.png", bbox_inches = "tight")
