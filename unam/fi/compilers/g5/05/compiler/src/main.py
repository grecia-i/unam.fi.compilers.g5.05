from modules.lexer import Lexer
from modules.parser import Parser
from modules.semantic import SemanticAnalyzer, SemanticError
from modules.savePrint import *
from modules.tac_generator import TACGenerator
from nltk.tree import Tree
from nltk import Tree as NLTKTree
import sys
from copy import copy
import os.path
from pathlib import Path
from rply import errors

def debug_ast_structure(ast, indent=0):
    """Función para debuggear la estructura del AST"""
    if isinstance(ast, Tree):
        print("  " * indent + f"Tree: {ast.label()} (len: {len(ast)})")
        for i, child in enumerate(ast):
            print("  " * (indent + 1) + f"Child {i}:")
            debug_ast_structure(child, indent + 2)
    elif isinstance(ast, list):
        print("  " * indent + f"List: (len: {len(ast)})")
        for i, item in enumerate(ast):
            print("  " * (indent + 1) + f"Item {i}:")
            debug_ast_structure(item, indent + 2)
    else:
        print("  " * indent + f"Value: {ast}")

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
# --- PHASE 3: TAC GENERATION ---
                print("\nStarting TAC Generation...")
                tac_generator = TACGenerator()
                
                # Verificar que el árbol no sea None
                if parse_tree is None:
                    print("ERROR: parse_tree is None!")
                    return
                
                tac_code = tac_generator.generate_tac(parse_tree)
                
                # Verificar el código TAC generado
                print(f"TAC lines generated: {len(tac_code)}")
                
                if len(tac_code) == 0:
                    print("WARNING: No TAC code generated!")
                    print("This might be due to:")
                    print("1. AST structure different than expected")
                    print("2. No functions found in the code")
                    print("3. Empty program")
                else:
                    print("\nTAC Generation Success!")
                
                # Guardar TAC en archivo
                tac_output_path = project_root / f"{Path(sourceFile).stem}_tac.txt"
                with open(tac_output_path, 'w', encoding='utf-8') as f:
                    f.write("THREE ADDRESS CODE (TAC):\n")
                    f.write("=" * 50 + "\n")
                    for line in tac_code:
                        f.write(line + "\n")
                    if len(tac_code) == 0:
                        f.write("// No TAC code generated - check AST structure\n")
                
                # Mostrar TAC en consola
                print("\n" + "=" * 50)
                print("THREE ADDRESS CODE (TAC):")
                print("=" * 50)
                if len(tac_code) > 0:
                    for line in tac_code:
                        print(line)
                else:
                    print("// No TAC code generated")
                    print("// The AST structure might be different than expected")
                print("=" * 50)
                print(f"\nTAC saved to: {tac_output_path}")

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