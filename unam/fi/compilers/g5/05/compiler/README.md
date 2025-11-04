#  COMPILERS • 2026-1 #
This repository covers the work and projects related to the subject of compilers at the Faculty of Engineering, UNAM. The main objective is to develop a compiler using concepts learned during the semester for a simplified version of the GO programming language, the specifics of which are detailed in the report.

## Phases of the compiler
### Lexer
The programs implements a simple lexical analizer using [rply](https://pypi.org/project/rply/), it takes a source file as input and generates a token stream and a summary of said token stream.
The tokens are saved to a `.txt` file. 



### Parser / SDT
Using [rply's](https://pypi.org/project/rply/) parser generator the program defines our language's grammar and structure, for every production it assigns a semantic action and produces a node of the program's parse tree, this parse tree is outputed as a nltk style tree in src/program.txt, afterwards it starts a phase os semantic analysis to verify the context of every production.

### Requirements

- python 3.8+
- [rply](https://pypi.org/project/rply/)

    #### How to run
    Install the dependencies with:
    ```pip install rply```

    The path to the source file may be specified in one of two ways:
    - Directly as a command line argument: `python main.py <path to file>`
    - Interactively at the beginning of the programs execution

    If the source code is valid the program will output a summary of the tokens as well as a parse tree for the source file and save them to a `.txt` file

The project includes a few examples of both valid and no valid source files in the directory `tests`

***The report can be found in docs/Team05_Compilers_Lexer.pdf***

📄 [View the Report](doc/Team05_Compilers_Lexer.pdf)

