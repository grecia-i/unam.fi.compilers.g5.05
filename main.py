from Lexer.src.lexer import Lexer
import sys
from copy import copy
import os.path
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
            f"Token no valido en la línea: {lexError.getsourcepos().lineno}, columna: {lexError.getsourcepos().colno - 1}"
        )
        print(f"Línea completa:\n{line}")
    if not ERROR:
        print("\n\nThe program is lexically correct")
        lexer_init.summary()
        lexer_init.save_tokens_to_file("tokens.txt")


if __name__ == "__main__":
    main()
