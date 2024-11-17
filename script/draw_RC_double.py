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

def read_rocking_curve(filename):
    degree_list = []
    ival_list = []
    r_factor = 0.0
    with open(filename, "r") as fp:
        lines = fp.readlines()
        for line in lines:
            if line[0] == "#":
                if line[1] == "f":
                    r_factor = float((line.split())[2])
                continue
            v = line.split()
            degree_list.append(float(v[0]))
            ival_list.append(float(v[1]))
    return degree_list, ival_list, r_factor

def read_exp(filename):
    degree_list, exp_list = np.loadtxt(filename, unpack=True)
    exp_list /= np.sum(exp_list)
    return degree_list, exp_list

degree_list_ini, I_ini_list, R_ini = read_rocking_curve("RockingCurve_ini.txt")
degree_list_con, I_con_list, R_con = read_rocking_curve("RockingCurve_con.txt")
degree_list, exp_list = read_exp("experiment.txt")

print("len(degree_list):", len(degree_list))
print("len(exp_list):", len(exp_list))
print("len(I_ini_list):", len(I_ini_list))
print("len(I_con_list):", len(I_con_list))

plt.plot(degree_list, exp_list, marker = "$o$", linewidth = 0.0, color = "red", label = "experiment")
plt.plot(degree_list, I_ini_list, marker = "None", color = "blue", label = "initial(R-factor = %f)"%(R_ini))
plt.plot(degree_list, I_con_list, marker = "None", color = "green", label = "converged(R-factor = %f)"%(R_con))
plt.xlabel("degree")
plt.ylabel("I")
plt.legend()
plt.savefig("RC_double.png", bbox_inches = "tight")

with open("RC_double.txt", "w") as fp:
    fp.write("#R-factor(initial) = %f\n"%(R_ini))
    fp.write("#R-factor(converged) = %f\n"%(R_con))
    fp.write("#degree experiment I(initial) I(converged)\n")
    for i in range(len(degree_list)):
        fp.write("%f %f %f %f\n"%(degree_list[i], exp_list[i], I_ini_list[i], I_con_list[i]))
