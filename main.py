from Lexer.src.Lexer import Lexer
import sys
from copy import copy
import os.path
from rply import errors

def main():
    #print("Total arguments:", len(sys.argv))
    #print("Script name:", sys.argv[0])
    #print("Arguments:", sys.argv[1:])
    if len(sys.argv)==1:
        sourceFile = input('Enter the source file\'s name: ')
    elif len(sys.argv)==2:
        sourceFile = sys.argv[1]
    else:
        print('Too many arguments')
        sys.exit()
    
    if not os.path.isfile(sourceFile):
        print("\n Could not find the file \'"+sourceFile+"\'")

    print("Hello World!")

    fileContents = open(sourceFile, "r").readlines()

    # --- Lexer ---
    

if __name__ == "__main__":
    main()
