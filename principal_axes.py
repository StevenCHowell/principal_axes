#! /usr/bin/env python

# Author: Pierre Poulain
# Contributors: Justine Guegan, Edithe Selwa, Steven C. Howell

# This Python script computes principal axes from a PDB file
# Itproduces a .pml script for a nice rendering with PyMOL

#==========================================================================
# import required modules
#==========================================================================
import sys
import os.path
import numpy

#==========================================================================
# define data or hard-coded parameters
#==========================================================================
# scale factor to enhance the length of axis in Pymol
scale_factor = 20

#==========================================================================
# define functions
#==========================================================================

#==========================================================================
def read_pdb_xyz(pdb_name):
    """
    reads atomic coordinates of C-alpha atoms in a .pdb file
    returns:
        [[x1 y1 z1]
         [x2 y2 z2]
         [.. .. ..]
         [xn yn zn]]
    """
    xyz = []
    with open(pdb_name, 'r') as pdb_file:
        for line in pdb_file:
            if line.startswith("ATOM"):
                # extract x, y, z coordinates for carbon alpha atoms
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                if line[12:16].strip() == "CA":
                    xyz.append([x, y, z])
    return xyz

#==========================================================================
# start program
#==========================================================================

# check if argument is there
if len(sys.argv) == 2:
    pdb_name = sys.argv[1]
else:
    message = """
    ERROR: missing pdb filename as argument
    usage: %s file.pdb""" %(sys.argv[0])
    sys.exit(message)

# check if argument is an existing file
if not os.path.exists(pdb_name):
    sys.exit("ERROR: file %s does not seem to exist" %(pdb_name))


#--------------------------------------------------------------------------
# compute principal axes
#--------------------------------------------------------------------------
# read pdb
xyz = read_pdb_xyz(pdb_name)
print("%d CA atomes found if %s" %(len(xyz), pdb_name))

#create coordinates array
coord = numpy.array(xyz, float)

# compute geometric center
center = numpy.mean(coord, 0)
print("Coordinates of the geometric center:\n", center)

# center with geometric center
coord = coord - center

# compute principal axis matrix
coord2 = numpy.dot(coord.transpose(), coord)
numpy.fill_diagonal(coord2, coord2.diagonal() - coord2.trace())
inertia = -coord2
e_values, e_vectors = numpy.linalg.eig(inertia)
# warning eigenvalues are not necessary ordered!
# http://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.eig.html
print("(Unordered) eigenvalues:")
print(e_values)
print("(Unordered) eigenvectors:")
print(e_vectors)

#--------------------------------------------------------------------------
# order eigenvalues (and eigenvectors)
#
# axis1 is the principal axis with the biggest eigenvalue (eval1)
# axis2 is the principal axis with the second biggest eigenvalue (eval2)
# axis3 is the principal axis with the smallest eigenvalue (eval3)
#--------------------------------------------------------------------------
order = numpy.argsort(e_values)
eval3, eval2, eval1 = e_values[order]
axis3, axis2, axis1 = e_vectors[:, order].transpose()

print("Inertia axis are now ordered !")

#--------------------------------------------------------------------------
# center axes to the geometric center of the molecule
# and rescale them by order of eigenvalues
#--------------------------------------------------------------------------
# the large vector is the first principal axis
point1 = 3 * scale_factor * axis1 + center
# the medium vector is the second principal axis
point2 = 2 * scale_factor * axis2 + center
# the small vector is the third principal axis
point3 = 1 * scale_factor * axis3 + center

#--------------------------------------------------------------------------
# create .pml script for a nice rendering in Pymol
#--------------------------------------------------------------------------
pymol_name = pdb_name.replace(".pdb", "_axes.pml")
with open(pymol_name, "w") as pymol_file:
    pymol_file.write(
        """
        from cgo import *
        axis1=  [ \
        BEGIN, LINES, \
        COLOR, 1.0, 0.0, 0.0, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        END ]
        axis2=  [ \
        BEGIN, LINES, \
        COLOR, 0.0, 1.0, 0.0, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        END ]
        axis3=  [ \
        BEGIN, LINES, \
        COLOR, 0.0, 0.0, 1.0, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        VERTEX, %8.3f, %8.3f, %8.3f, \
        END ]
        cmd.load_cgo(axis1, 'axis1')
        cmd.load_cgo(axis2, 'axis2')
        cmd.load_cgo(axis3, 'axis3')
        cmd.set('cgo_line_width', 4)
        """ %( \
                center[0], center[1], center[2], point1[0], point1[1], point1[2], \
                center[0], center[1], center[2], point2[0], point2[1], point2[2], \
                center[0], center[1], center[2], point3[0], point3[1], point3[2]))

#--------------------------------------------------------------------------
# create .pml script for nice rendering in Pymol
# output usage
#--------------------------------------------------------------------------
print("\nThe first principal axis is in red")
print("coordinates: ", axis1)
print("eigenvalue: ", eval1)

print("\nThe second principal axis is in green")
print("coordinates:", axis2)
print("eigenvalue:", eval2)

print("\nThe third principal axis is in blue")
print("coordinates:", axis3)
print("eigenvalue:", eval3)

print("\nYou can view principal axes with PyMOL:")
print("pymol %s %s" %(pymol_name, pdb_name))
