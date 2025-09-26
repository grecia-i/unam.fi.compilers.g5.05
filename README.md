#  COMPILERS • 2026-1 #
This repository covers the work and projects related to the subject of compilers at the Faculty of Engineering, UNAM. The main objective is to develop a compiler using concepts learned during the semester. 

## Phases of the compiler
### Lexer
The programs implements a simple lexical analizer using [rply](https://pypi.org/project/rply/), it takes a source file as input and generates a token stream and a summary of said token stream.
The tokens are saved to a `.txt` file. 

The syntax used in the source file is a simplified version of the GO programming language, the specifics of which are detailed in the report.

Requirements:
- python 3.8+
- [rply](https://pypi.org/project/rply/)

    #### How to run
    Install the dependencies with:
    ```pip install rply```

    The path to the source file may be specified in one of two ways:
    - Directly as a command line argument: `python main.py <path to file>`
    - Interactively at the beginning of the programs execution

    If the source code is valid the program will output a summary of the tokens and save them to a `.txt` file

The project includes a few examples of both valid and not valid source files in the directory `tests`

***The report can be found in docs/Team05_Compilers_Lexer.pdf***

📄 [View the Report](docs/Team05_Compilers_Lexer.pdf)

