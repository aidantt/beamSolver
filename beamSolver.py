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
import logging # for logging functionality

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

# setup logging functionality
def setupLogging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # set format
    formatter = logging.Formatter('%(message)s')

    # file handler
    file_handler = logging.FileHandler("output.txt", mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# read, define, return mesh data
def readMesh(meshData : list[str], 
             connectivity : list[str]
            ) -> tuple[int, int, dict[int, float], list[tuple[int, int, int]]]:
    logOut.info("Parsing mesh data...")

    # strip each line
    meshData = [line.strip() for line in meshData]
    connectivity = [line.strip() for line in connectivity]
    
    # first handle meshData
    # line 1 is the number of nodes and elements
    numNodes, numElements = tuple(map(int, meshData[0].split()))
    # lines 2-end are the coordinates of each node
    nodeCoord = {}
    for line in meshData[1:]:
        # split each line by whitespace
        node = line.split()
        nodeNum = int(node[0])
        nodePosition = float(node[1])
        nodeCoord[nodeNum] = nodePosition

    # then connectivity
    # for each line, split by whitespace and gather into integer tuples
    connectivityList = []
    for line in connectivity:
        element = line.split()
        elementNum = int(element[0])
        node1 = int(element[1])
        node2 = int(element[2])
        connectivityList.append((elementNum, node1, node2))

    # print the extracted values to log
    logOut.info(f"\tNumber of nodes: {numNodes}")
    logOut.info(f"\tNumber of elements: {numElements}")
    logOut.info(f"\tNode coordinates:")
    for node, coordinate in nodeCoord.items():
        logOut.info(f"\t\tNode {node} at position {coordinate}")
    logOut.info(f"\tElement connectivity:")
    for element in connectivityList:
        logOut.info(f"\t\t{element[0]} \t {element[1]} \t {element[2]}")
    logOut.info("\n")
    # return the extracted values
    return numNodes, numElements, nodeCoord, connectivityList

# read and return material properties
def readProperties(properties : list[str]) -> tuple[float, float, float]:
    logOut.info("Parsing material properties...")

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

    # print the extracted values to log
    logOut.info(f"\tYoung's Modulus: {youngsModulus}")
    logOut.info(f"\tHeight: {height}")
    logOut.info(f"\tWidth: {width}\n")

    # return the extracted values
    return youngsModulus, height, width

# read and return kinematic constraints
def readConstraints(constraints : list[str]) -> tuple[int, list[int]]:
    logOut.info("Parsing constraints...")

    # strip each line
    constraints = [line.strip() for line in constraints]
    # first line is always the number of constraints
    numConstraints = int(constraints[0])
    # second line is the list of zeroed DOFs
    constraintList = constraints[1].split()
    zeroDofList = list(map(int, constraintList))

    # print the extracted values to log
    logOut.info(f"\tNumber of constraints: {numConstraints}")
    logOut.info(f"\tZeroed DOFs: {zeroDofList}\n")

    # return the extracted values
    return numConstraints, zeroDofList

# read and return point loads
def readLoads(loads : list[str]) -> tuple[int, list[tuple[int, float]]]:
    logOut.info("Parsing point loads...")

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
    
    # print the extracted values to log
    logOut.info(f"\tNumber of point loads: {numPointLoads}")
    logOut.info(f"\tPoint load coordinates (by DoF): {loadCoord}\n")

    # return the extracted values
    return numPointLoads, loadCoord

# given nodes and connectivity, calculate DOFs for the element (assembly vector)
def getElementDOF(node1 : int, node2 : int) -> list[int]:
    # given connectivity of the element, return assembly vector,
    # i.e. global DoFs corresponding to the local element nodes

    # under the convention that each node has 2 DoFs (translation and rotation),
    # global DoFs are a simple linear mapping of the local node numbers.
    # convert nodes to their index in the node graph, then map to global DoFs
    localIndex = [node1-1, node2-1]
    globalIndex = [[2*i, 2*i+1] for i in localIndex]
    # flatten the list of lists to a single list
    globalIndex = [item for sublist in globalIndex for item in sublist]

    return globalIndex

# given nodes and connectivity, calculate the local stiffness matrix
def getElementK(E, I, L) -> np.ndarray:
    localK = (E*I) * np.array([[12/L**3, 6/L**2, -12/L**3, 6/L**2],
                               [6/L**2, 4/L, -6/L**2, 2/L],
                               [-12/L**3, -6/L**2, 12/L**3, -6/L**2],
                               [6/L**2, 2/L, -6/L**2, 4/L]])
    return localK

# given zero dofs, apply kinematic constraints to the global stiffness matrix
def imposeConstraints():
    return None

# given beam parameters, geometry, connectivity, assemble the global stiffness
# matrix from the local stiffness matrices of each element
def assembleGlobalStiffnessMatrix(numNodes : int, 
                                  connectivityList : list[tuple[int, int, int]], 
                                  nodeCoord : dict[int, float],
                                  youngsModulus : float,
                                  inertia : float) -> np.ndarray:
    # in order to calculate the global stiffness matrix, loop over each element
    # and calculate the local stiffness matrix.
    # then, after calculation of each local stiffness matrix, append values
    # to the global matrix, utilizing the penalty method along the diagnonal
    # to account for the constraints where applicable.

    logOut.info("Assembling global stiffness matrix...")

    # initialize the global stiffness matrix as a square matrix with dimensions
    # equal to numnodes * 2 (translation and rotation DoFs for each node)
    dofSize = numNodes * 2
    globalK = np.zeros((dofSize, dofSize))

    # from the above definition, the DoFs of the beam are indexed
    # from 0 -> 2*numNodes-1

    # loop over each element via the connectivity
    for element in connectivityList:
        # element is a tuple of (elementNum, node1, node2).
        # under this convention, node1 is the first node in the element
        # and node2 is the second node in the element.
        # extract the nodes from the tuple
        node1 = element[1]
        node2 = element[2]

        # pass these nodes to getElementDOF() to get the global DoFs from the
        # local element nodes
        assemblyVector = getElementDOF(node1, node2)
        logOut.info(f"\tElement {element[0]} Assembly Vector: {assemblyVector}")

        # get the length of the current element via the node coordinates
        length = np.abs(nodeCoord[node2] - nodeCoord[node1])
        logOut.info(f"\tElement {element[0]} Length: {length}")

        # now assemble local stiffness matrix
        localK = getElementK(youngsModulus, inertia, length)
        logOut.info(f"\tElement {element[0]} Local Stiffness Matrix:\n{localK}\n")

        # use localK in conjunction with the assembly vector to build
        # the global stiffness matrix.
        # np.ix_() allows for extraction and operation on submatrices
        # given a list of indices to act on.
        # effectively, this statement selectively extracts the rows and columns
        # of the global stiffness submatrix corresponding to the local element,
        # then appends the local values to the global matrix.
        globalK[np.ix_(assemblyVector, assemblyVector)] += localK

    # log the global stiffness matrix
    logOut.info(f"Global Stiffness Matrix:\n{globalK}\n")
    return globalK

# main function
if __name__ == "__main__":
    # intro
    splash()
    
    # setup a logger to write to console and output file simultaneously
    logOut = setupLogging()
    
    # read in CLI inputs
    # if none given, use default input file
    args = readCLI()
    filename = args.input if args.input else "input.txt"
    logOut.info(f"Reading input file: {filename}\n")

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

    # before global assembly, calculate 2nd moment of area
    # since we assume rectangular cross-section and constant cross-section
    # across the beam, this value is constant and used for each element
    I = (width*height**3)/12
    logOut.info(f"2nd Moment of Area for Rectangular Cross-Section: {I:.6g}\n")

    # now, assemble the global stiffness matrix
    globalK = assembleGlobalStiffnessMatrix(numNodes, connectivityList, nodeCoord, youngsModulus, I)
