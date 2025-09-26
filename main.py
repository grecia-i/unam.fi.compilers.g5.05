from Lexer.src.lexer import Lexer
import sys
from copy import copy
import os.path
from pathlib import Path
from rply import errors



def main():
    if len(sys.argv) == 1:
        sourceFile = input("Enter the source file's name: ")
    elif len(sys.argv) == 2:
        sourceFile = sys.argv[1]
    else:
        print("Too many arguments")
        sys.exit()

    if not os.path.isfile(sourceFile):
        print("\n Could not find the file '" + sourceFile + "'")

    # --- Lexer ---
    ERROR = False
    lexer_init = Lexer()
    lexer = lexer_init.get_lexer()

    with open(sourceFile, "r", encoding="utf-8") as f:
        source_code = f.read()
        source_lines = source_code.splitlines()

    tokens = lexer.lex(source_code)
    try:
        for token in copy(tokens):
            lexer_init.categorize_token(token)
    except errors.LexingError as lexError:
        ERROR = True
        line = source_lines[lexError.getsourcepos().lineno - 1]
        print(
            f"Invalid token at line: {lexError.getsourcepos().lineno}, column: {lexError.getsourcepos().colno - 1}"
        )
        print(f"Complete line:\n{line}")
    if not ERROR:
        print("\n\nThe program is lexically correct")
        lexer_init.summary()
        project_root = Path(__file__).parent.resolve()
        out_path =  project_root / f"{Path(sourceFile).stem}.txt" 
        lexer_init.save_tokens_to_file(str(out_path))

if __name__ == "__main__":
    main()
