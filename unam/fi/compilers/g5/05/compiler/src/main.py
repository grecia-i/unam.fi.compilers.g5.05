from modules.lexer import Lexer
from modules.parser import Parser
from modules.semantic import SemanticAnalyzer, SemanticError
# ---  FASE 3 ---
from modules.codegen import CCodeGenerator
import subprocess
# ----------------------------------------
from nltk import Tree as NLTKTree
import sys
from copy import copy
import os.path
from pathlib import Path
from rply import errors
from modules.savePrint import *

def main():
    if len(sys.argv) == 1:
        sourceFile = input("Enter the source file's name: ")
    elif len(sys.argv) == 2:
        sourceFile = sys.argv[1]
    else:
        print("Too many arguments")
        sys.exit()

    # Quitar comillas si el usuario las puso en la ruta (Windows a veces lo hace)
    sourceFile = sourceFile.strip('"')

    if not os.path.isfile(sourceFile):
        print("\n Could not find the file '" + sourceFile + "'")
        sys.exit() 

    # --- Lexer ---
    ERROR = False
    lexer_init = Lexer()
    lexer = lexer_init.get_lexer()

    with open(sourceFile, "r", encoding="utf-8") as f:
        source_code = f.read()
        source_lines = source_code.splitlines()

    # --- INITIAL LEXICAL CHECK ---
    try:
        list(lexer.lex(source_code))
    except errors.LexingError as lexError:
        ERROR = True
        line = source_lines[lexError.getsourcepos().lineno - 1]
        print(f"Invalid token at line: {lexError.getsourcepos().lineno}")
        print(f"Complete line:\n{line}")
        
    # --- CONTINUE IF LEXICALLY CORRECT ---
    if not ERROR:
        print("\n\nThe program is lexically correct")
        
        # --- Lexical Summary ---
        summary_tokens = lexer.lex(source_code)
        for token in summary_tokens:
            lexer_init.categorize_token(token)
        
        project_root = Path(__file__).parent.resolve()
        out_path =  project_root / f"{Path(sourceFile).stem}.txt" 
        tokens_summary_path = str(out_path).replace(".txt", "_tokens.txt") # Guardar tokens aparte
        # lexer_init.tokens_to_file(tokens_summary_path) 
        print(f"Tokens summary written to: {out_path}")

        # --- PARSING AND SEMANTIC PHASES ---
        parser_init = Parser()
        parser = parser_init.get_parser()
        
        parse_tree = None 

        try:
            # --- PHASE 1: SYNTACTIC ANALYSIS (PARSING) ---
            print("\nStarting Parsing (Syntactic)...")
            parse_tree = parser.parse(lexer.lex(source_code))
            print("Parsing Success!") 
            print_and_save_tree(parse_tree, str(out_path))
            print(f"Parse tree appended to: {out_path}")
            
        except errors.ParsingError as parseError:
            print("\n--- SYNTAX ERROR ---")
            print("Parsing error...") 
            ERROR = True
            pos = parseError.getsourcepos()
            print(f"Parsing error at line {pos.lineno}, column {pos.colno}")
            line = source_lines[pos.lineno - 1]
            print(f"Complete line:\n{line}")

        # --- PHASE 2 & 3: SEMANTIC ANALYSIS & CODE GEN ---
        if not ERROR:
            try:
                # --- FASE 2: SEMÁNTICO ---
                print("\nStarting Semantic Analysis (SDT)...")
                analyzer = SemanticAnalyzer()
                analyzer.visit(parse_tree)
                print("\nSDT Verified!") 

                # --- FASE 3: CODE GENERATION (C) ---
                print("\nGenerating C code...")
                generator = CCodeGenerator()
                generator.visit(parse_tree)
                
                # 1. Save the .c file in the same folder as the .go file
                c_path = Path(sourceFile).with_suffix('.c')
                with open(c_path, "w") as f:
                    f.write(generator.get_code())
                print(f"C code generated in: {c_path}")
                
                # 2. Compile with GCC (Automatic Attempt)
                try:
                    exe_path = Path(sourceFile).with_suffix('.exe')
                    print(f"Compiling with GCC -> {exe_path.name}...")
                    
                    # System call for gcc
                    subprocess.run(["gcc", str(c_path), "-o", str(exe_path)], check=True)
                    print("¡Successful Compilation!")
                    
                    # 3. Run (Optional)
                    print(f"\n--- EXECUTING {exe_path.name} ---")
                    subprocess.run([str(exe_path)]) 
                    print("\n--- END OF EXECUTION ---")
                    
                except FileNotFoundError:
                    print("\nWARNING: The 'gcc' command was not found.")
                    print(f"File C was indeed generated in: {c_path}")
                    print("You can compile it manually or install MinGW.")
                except subprocess.CalledProcessError:
                    print("\nERROR: GCC failed to compile the generated C file.")

            except SemanticError as e:
                print("\n--- SEMANTIC (SDT) ERROR ---")
                print("Parsing Success!") 
                print(f"SDT error... {e}")
            
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                import traceback
                traceback.print_exc() 

if __name__ == "__main__":
    main()