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

if __name__ == "__main__":
    splash()
    print("works")