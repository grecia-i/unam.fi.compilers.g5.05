#  COMPILERS • 2026-1 #
This repository covers the work and projects related to the subject of compilers at the Faculty of Engineering, UNAM. The main objective is to develop a compiler using concepts learned during the semester for a simplified version of the GO programming language, the specifics of which are detailed in the report.

## Phases of the compiler
### Lexer
The programs implements a simple lexical analizer using [rply](https://pypi.org/project/rply/), it takes a source file as input and generates a token stream and a summary of said token stream.
The tokens are saved to a `.txt` file. 



### Parser / SDT
Using [rply's](https://pypi.org/project/rply/) parser generator the program defines our language's grammar and structure, for every production it assigns a semantic action and produces a node of the program's parse tree, this parse tree is outputed as a nltk style tree in src/program.txt, afterwards it starts a phase of semantic analysis to verify the context of every production.

### Code generation
For this phase we followed two parallel methodologies:
- **TAC -> Assembly:** The SDT is converted to TAC and then to assembly code, this code is then assembled using [NASM](https://www.nasm.us/) and linked with [GCC](https://gcc.gnu.org/).

- **SDT -> C:** The operations in the SDT are converted to C code constructs in standard C syntax, this intermediate C code is then processed by [GCC](https://gcc.gnu.org/).



### Requirements

- python 3.8+
- [rply](https://pypi.org/project/rply/)
- [GCC](https://gcc.gnu.org/)

    #### How to run
    Install the dependencies with:
    ```pip install rply```
    ```pip install nltk```

    The path to the source file may be specified in one of two ways:
    - Directly as a command line argument: `python main.py <path to file>`
    - Interactively at the beginning of the programs execution

    If the source code is valid the program will output a summary of the tokens as well as a parse tree for the source file and save them to a `.txt` file

    #### Flags
    - --f: Verbose output, generates text output for all phases and saves the intermediate code file in `compiler/build/`. 

The project includes a few examples of both valid and no valid source files in the directory `test`

***The reports for every phase can be found in unam/fi/compilers/g5/05/compiler/doc/***

📄 [Lexer](unam/fi/compilers/g5/05/compiler/doc/Team05-Compilers-Lexer.pdf)

📄 [Parser](unam/fi/compilers/g5/05/compiler/doc/05-Compilers-Parser.pdf)

📄 [Compiler](unam/fi/compilers/g5/05/compiler/doc/05-Compilers-Final.pdf)

