from modules.lexer import Lexer
from modules.parser import Parser
from modules.semantic import SemanticAnalyzer, SemanticError
from modules.savePrint import *
from nltk import Tree as NLTKTree
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
        sys.exit() # Exit if file not found

    # --- Lexer ---
    ERROR = False
    lexer_init = Lexer()
    lexer = lexer_init.get_lexer()

    with open(sourceFile, "r", encoding="utf-8") as f:
        source_code = f.read()
        source_lines = source_code.splitlines()

    # --- INITIAL LEXICAL CHECK ---
    try:
        # Test the lexer stream. list() consumes it.
        list(lexer.lex(source_code))
    except errors.LexingError as lexError:
        ERROR = True
        line = source_lines[lexError.getsourcepos().lineno - 1]
        print(
            f"Invalid token at line: {lexError.getsourcepos().lineno}, column: {lexError.getsourcepos().colno - 1}"
        )
        print(f"Complete line:\n{line}")
        
    # --- CONTINUE IF LEXICALLY CORRECT ---
    if not ERROR:
        print("\n\nThe program is lexically correct")
        
        # --- Lexical Summary ---
        # (Needs a new token stream as the first was consumed)
        summary_tokens = lexer.lex(source_code)
        for token in summary_tokens:
            lexer_init.categorize_token(token)
        # lexer_init.summary()
        
        project_root = Path(__file__).parent.resolve()
        out_path =  project_root / f"{Path(sourceFile).stem}.txt" 
        tokens_to_file(lexer_init.category, lexer_init.token_count, str(out_path))

        # --- PARSING AND SEMANTIC PHASES ---
        parser_init = Parser()
        parser = parser_init.get_parser()
        
        parse_tree = None # To store the AST

        try:
            # --- PHASE 1: SYNTACTIC ANALYSIS (PARSING) ---
            print("\nStarting Parsing (Syntactic)...")
            
            # rply token streams are single-use, re-generate
            parse_tree = parser.parse(lexer.lex(source_code))
            
            # Required project output
            print("Parsing Success!") 
            print_and_save_tree(parse_tree, str(out_path))
            
        except errors.ParsingError as parseError:
            # --- SYNTAX ERROR ---
            print("\n--- SYNTAX ERROR ---")
            print("Parsing error...") # Required output
            ERROR = True
            pos = parseError.getsourcepos()
            print(
                f"Parsing error at line {pos.lineno}, column {pos.colno}"
            )
            line = source_lines[pos.lineno - 1]
            print(f"Complete line:\n{line}")

        # --- PHASE 2: SEMANTIC ANALYSIS (SDT) ---
        # This block ONLY runs if PHASE 1 (Parsing) was successful
        if not ERROR:
            try:
                print("\nStarting Semantic Analysis (SDT)...")
                analyzer = SemanticAnalyzer()
                analyzer.visit(parse_tree) # Execute your semantic code
                
                # If we get here, everything passed
                print("\nSDT Verified!") # Required output

            except SemanticError as e:
                # --- SEMANTIC (SDT) ERROR ---
                print("\n--- SEMANTIC (SDT) ERROR ---")
                # Required outputs:
                print("Parsing Success!") 
                print(f"SDT error... {e}")
            
            except Exception as e:
                # Catch other unexpected errors from semantic.py
                print(f"\nUnexpected error in semantic analyzer: {e}")

if __name__ == "__main__":
    main()