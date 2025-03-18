# beamSolver - Aidan Timofte
# perform Finite Element Analysis (FEA) on a simple beam.

# given a set of nodes and elements, generate a mesh.
# apply material properties, constraints, and loads.
# solve for the deflection field using FEA.

# Inputs:
#   - node placement
#   - element connectivity
#   - material properties
#   - constraints
#   - point loads

# Outputs:
#   - deflection field
#   - FEA mesh
#   - local & global stiffness matrices
#   - postprocessing (stress, strain fields, etc...)

# given a .txt file with a designated syntax, extract all inputs

# import necessary libraries
import numpy as np # for math, matrix operations, inverse matrices
import argparse # for command line arguments

# Intro program
def splash() -> None:
    with open("splash.txt", "r") as splash:
        for line in splash:
            print(line,end="")
    print("\n")

# initialize parser and read CLI inputs
def readCLI() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Perform Finite Element Analysis on a simple beam.")
    parser.add_argument("-i", "--input", type=str, nargs='?', help="Input .txt file with designated syntax.")
    return parser.parse_args()

# read, define, return mesh data
def readMesh(meshData : list[str], connectivity : list[str]) -> tuple[int, int, list[tuple[int, float]], list[tuple[int, int, int]]]:
    print("Parsing mesh data...")

    # strip each line
    meshData = [line.strip() for line in meshData]
    connectivity = [line.strip() for line in connectivity]
    
    # first handle meshData
    # line 1 is the number of nodes and elements
    numNodes, numElements = tuple(map(int, meshData[0].split()))
    # lines 2-end are the coordinates of each node
    nodeCoord = []
    for line in meshData[1:]:
        # split each line by whitespace
        node = line.split()
        nodeNum = int(node[0])
        nodePosition = float(node[1])
        nodeCoord.append((nodeNum, nodePosition))

    # then connectivity
    # for each line, split by whitespace and gather into integer tuples
    connectivityList = []
    for line in connectivity:
        element = line.split()
        elementNum = int(element[0])
        node1 = int(element[1])
        node2 = int(element[2])
        connectivityList.append((elementNum, node1, node2))

    # print the extracted values
    print(f"\tNumber of nodes: {numNodes}")
    print(f"\tNumber of elements: {numElements}")
    print(f"\tNode coordinates:")
    for node in nodeCoord:
        print(f"\t\tNode {node[0]} at position {node[1]}")
    print(f"\tElement connectivity:")
    for element in connectivityList:
        print(f"\t\t{element[0]} \t {element[1]} \t {element[2]}")
    print()

    # return the extracted values
    return numNodes, numElements, nodeCoord, connectivityList

# read and return material properties
def readProperties(properties : list[str]) -> tuple[float, float, float]:
    print("Parsing material properties...")

    # per syntax, properties is always a single line
    # strip each line
    properties = [line.strip() for line in properties]
    # split the line by whitespace
    propertyList = properties[0].split()
    # convert each value to a float
    # python floats are 8-byte by default
    youngsModulus = float(propertyList[0])
    height = float(propertyList[1])
    width = float(propertyList[2])

    # print the extracted values
    print(f"\tYoung's Modulus: {youngsModulus}")
    print(f"\tHeight: {height}")
    print(f"\tWidth: {width}\n")

    # return the extracted values
    return youngsModulus, height, width

# read and return kinematic constraints
def readConstraints(constraints : list[str]) -> tuple[int, list[int]]:
    print("Parsing constraints...")

    # strip each line
    constraints = [line.strip() for line in constraints]
    # first line is always the number of constraints
    numConstraints = int(constraints[0])
    # second line is the list of zeroed DOFs
    constraintList = constraints[1].split()
    zeroDofList = list(map(int, constraintList))

    # print the extracted values
    print(f"\tNumber of constraints: {numConstraints}")
    print(f"\tZeroed DOFs: {zeroDofList}\n")

    # return the extracted values
    return numConstraints, zeroDofList

# read and return point loads
def readLoads(loads : list[str]) -> tuple[int, list[tuple[int, float]]]:
    print("Parsing point loads...")

    # strip each line
    loads = [line.strip() for line in loads]
    # extract number of point loads from line 1
    numPointLoads = int(loads[0])
    # lines 2-end are the coordinates of point loads by dof
    loadCoord = []
    for line in loads[1:]:
        # split each line by whitespace
        loadList = line.split()
        dof = int(loadList[0])
        loadMagnitude = float(loadList[1])
        loadCoord.append((dof, loadMagnitude))
    
    # print the extracted values
    print(f"\tNumber of point loads: {numPointLoads}")
    print(f"\tPoint load coordinates (by DoF): {loadCoord}\n")

    # return the extracted values
    return numPointLoads, loadCoord

# main function
if __name__ == "__main__":
    splash()
    
    # read in CLI inputs
    # if none given, use default input file
    args = readCLI()
    filename = args.input if args.input else "input.txt"
    print(f"Reading input file: {filename}\n")

    # open and parse input file based on pre-defined syntax
    with open(filename, "r") as file:
        # read in all lines of text as a list of strings
        lines = file.readlines()
        # separate this list into sections based on lines 
        # where only '\n' is present
        sections = []
        sublist = []
        for line in lines:
            if line == '\n':
                sections.append(sublist)
                sublist = []
            else:
                sublist.append(line)
        # append the last sublist
        sections.append(sublist)

        # for clarity, unpack the sections into separate lists
        meshData = sections[0]
        connectivity = sections[1]
        properties = sections[2]
        constraints = sections[3]
        loads = sections[4]

    # out of the with block, all file operations are closed

    # pass the parameter lists to their respective functions, 
    # then return all extracted data
    numNodes, numElements, nodeCoord, connectivityList = readMesh(meshData, connectivity)
    youngsModulus, height, width = readProperties(properties)
    numConstraints, zeroDofList = readConstraints(constraints)
    numPointLoads, loadCoord = readLoads(loads)