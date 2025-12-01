from modules.lexer import Lexer
from modules.parser import Parser
from modules.semantic import SemanticAnalyzer, SemanticError
from modules.utilities import *
from modules.codegen import CCodeGenerator
from modules.tac_generator import TACGenerator
from nltk.tree import Tree

import subprocess
# ----------------------------------------
from nltk import Tree as NLTKTree
import sys
from copy import copy
import os.path
from pathlib import Path
from rply import errors

def debug_ast_structure(ast, indent=0):
    """Debug function to print the structure of the AST."""
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
    generate_files = True  # Default: generate txt and c files
    debug_mode = False     # Flag detail debug
    flags = []
    
    # Parse flags
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--f":
            generate_files = True
        elif sys.argv[i] == "--debug":
            debug_mode = True
        elif sys.argv[i].startswith("--"):
            flags.append(sys.argv[i])
        else:
            sourceFile = sys.argv[i]
        i += 1
    
    # no --f, disable file generation
    if "--f" not in sys.argv:
        generate_files = False

    # no source file provided
    if 'sourceFile' not in locals():
        if len(sys.argv) == 1:
            sourceFile = input("Enter the source file's name: ")
        else:
            print("Usage: python main.py [--f] [--debug] <sourceFile.go>")
            print("\nFlags:")
            print("  --f      Generate intermediate files (.txt, .c)")
            print("  --debug  Generate semantic debug information")
            sys.exit(1)

    sourceFile = sourceFile.strip('"')
    build_dir = ensure_build_dir()
    output_name = get_output_filename(sourceFile)
    
    
    if not os.path.isfile(sourceFile):
        print(f"\nCould not find the file '{sourceFile}'")
        sys.exit() 
    
    # --- Lexer ---
    ERROR = False
    lexer_init = Lexer()
    lexer = lexer_init.get_lexer()

    with open(sourceFile, "r", encoding="utf-8") as f:
        source_code = f.read()
        source_lines = source_code.splitlines()

    # --- INITIAL LEXICAL CHECK ---
    output_messages = []
    try:
        list(lexer.lex(source_code))
        output_messages.append("Lexical analysis: SUCCESS")
        print(" Lexical analysis: SUCCESS")
    except errors.LexingError as lexError:
        ERROR = True
        line = source_lines[lexError.getsourcepos().lineno - 1]
        error_msg = f"Invalid token at line: {lexError.getsourcepos().lineno}"
        output_messages.append(f"Lexical analysis: ERROR - {error_msg}")
        print(f"\n LEXICAL ERROR")
        print(f"Invalid token at line: {lexError.getsourcepos().lineno}")
        print(f"Complete line:\n{line}")
        
    # --- CONTINUE IF LEXICALLY CORRECT ---
    if not ERROR:
        print("\nThe program is lexically correct")
        output_messages.append("\nThe program is lexically correct")
        
        # --- Lexical Summary ---
        summary_tokens = lexer.lex(source_code)
        for token in summary_tokens:
            lexer_init.categorize_token(token)
        
        # Save tokens summary to build folder
        if generate_files:
            tokens_to_file(lexer_init.category, lexer_init.token_count, sourceFile)
            print(f"Tokens summary saved to build folder")
        else:
            print(f"Tokens summary generated")

        # save log
        log_to_file_only(sourceFile, "lexical", output_messages, clear_first=True)

        # --- PARSING AND SEMANTIC PHASES ---
        parser_init = Parser()
        parser = parser_init.get_parser()
        
        parse_tree = None 
        parsing_messages = []

        try:
            # --- PHASE 1: SYNTACTIC ANALYSIS (PARSING) ---
            print("\nStarting Parsing (Syntactic)...")
            parsing_messages.append("Starting Parsing (Syntactic)...")
            
            parse_tree = parser.parse(lexer.lex(source_code))
            
            parsing_messages.append("Parsing Success!")
            print("Parsing Success!") 
            
            if generate_files:
                out_path = build_dir / f"{output_name}.txt"
                print_and_save_tree(parse_tree, sourceFile)
                parsing_messages.append(f"Parse tree written to: {out_path}")
                print(f"Parse tree saved to build folder")
            else:
                print("Parse tree generated")
                parsing_messages.append("Parse tree generated (not saved to file)")
            
            # Log to file
            log_to_file_only(sourceFile, "syntax", parsing_messages)

        except errors.ParsingError as parseError:
            parsing_messages.append("Parsing error...")
            pos = parseError.getsourcepos()
            error_msg = f"Parsing error at line {pos.lineno}, column {pos.colno}"
            parsing_messages.append(error_msg)
            
            print("\nSYNTAX ERROR")
            print(f"Parsing error at line {pos.lineno}, column {pos.colno}")
            line = source_lines[pos.lineno - 1]
            print(f"Complete line:\n{line}")
            
            ERROR = True
            write_output_log(sourceFile, "syntax", parsing_messages, is_error=True)

        # --- PHASE 2 & 3: SEMANTIC ANALYSIS & CODE GEN ---
        if not ERROR:
            try:
                # --- PHASE 2: SEMANTIC ---
                print("\nStarting Semantic Analysis (SDT)...")
                semantic_messages = ["Starting Semantic Analysis (SDT)..."]

                analyzer = SemanticAnalyzer()
                analyzer.set_echo_output(debug_mode)  # Only echo if debug flag is set

                if debug_mode:
                    analyzer.set_debug_mode(True)

                analyzer.visit(parse_tree)
                
                semantic_messages.append("SDT Verified!")
                print("SDT Verified!")
                
                # obtain semantic messages from analyzer
                if hasattr(analyzer, 'get_output_messages'):
                    analyzer_messages = analyzer.get_output_messages()
                    semantic_messages.extend(analyzer_messages)
                
                # save semantic debug info if --debug flag
                if debug_mode and hasattr(analyzer, 'get_debug_info'):
                    symbol_table_info = analyzer.get_symbol_table_info()
                    semantic_events = analyzer.get_semantic_events()
                    write_semantic_debug(sourceFile, symbol_table_info, semantic_events)
                    print(f"Semantic debug info saved")
                
                # save log
                log_to_file_only(sourceFile, "semantic", semantic_messages)

                # --- PHASE 3: CODE GENERATION ---
                print("\nStarting TAC Generation...")
                codegen_messages = ["Starting TAC Generation..."]
                
                if debug_mode:
                    tac_printer = print
                else:
                    tac_printer = lambda msg: None

                tac_generator = TACGenerator(printer=tac_printer)
                
                if parse_tree is None:
                    error_msg = "ERROR: parse_tree is None!"
                    codegen_messages.append(error_msg)
                    print(f"\n✗ {error_msg}")
                    write_output_log(sourceFile, "codegen", codegen_messages, is_error=True)
                    return
                
                tac_code = tac_generator.generate_tac(parse_tree)
                log_to_file_only(sourceFile, "tac", tac_code)

                # VERIFY TAC
                if len(tac_code) == 0:
                    warning_msg = "WARNING: No TAC code generated!"
                    codegen_messages.append(warning_msg)
                    print(f"⚠ {warning_msg}")
                else:
                    success_msg = "TAC Generation Success!"
                    codegen_messages.append(success_msg)
                    print(f"{success_msg}")
                
                # TAC to file (only if --f flag)
                if generate_files:
                    write_tac(tac_code, sourceFile)
                    codegen_messages.append(f"TAC saved to: {out_path}")
                    print(f"TAC saved to build folder")
                else:
                    info_msg = "TAC generated"
                    codegen_messages.append(info_msg)
                    print(f"{info_msg}")
                
                log_to_file_only(sourceFile, "codegen_tac", codegen_messages)

                # --- GENERATE C AND COMPILING
                print("\nGenerating C code...")
                cgen_messages = ["Generating C code..."]
                
                generator = CCodeGenerator()
                generator.visit(parse_tree)
                
                # Save c file (only if --f flag)
                c_path = build_dir / f"{output_name}.c"
                if generate_files:
                    with open(c_path, "w") as f:
                        f.write(generator.get_code())
                    cgen_messages.append(f"C code generated in: {c_path}")
                    print(f"C code generated in: {c_path}")
                else:
                    cgen_messages.append("C code generated (not saved to file)")
                    print("C code generated")
                    c_code = generator.get_code()
                    c_path = build_dir / f"{output_name}_temp.c"
                    with open(c_path, "w") as f:
                        f.write(c_code)
                
                # save log
                log_to_file_only(sourceFile, "codegen_c", cgen_messages)
                
                # -- GCC compiling
                try:
                    exe_path = build_dir / f"{output_name}.exe"
                    compilation_messages = [f"Compiling with GCC -> {exe_path.name}..."]
                    print(f"\nCompiling with GCC -> {exe_path.name}...")
                    
                    subprocess.run(["gcc", str(c_path), "-o", str(exe_path)], check=True)
                    
                    success_msg = "Successful Compilation!"
                    compilation_messages.append(success_msg)
                    print(f"{success_msg}")
                    
                    # compilation log
                    log_to_file_only(sourceFile, "compilation", compilation_messages)
                    
                    # --- EXECUTE
                    print(f"\n--- EXECUTING {exe_path.name} ---")
                    execution_messages = [f"--- EXECUTING {exe_path.name} ---"]
                    
                    result = subprocess.run([str(exe_path)], capture_output=True, text=True)
                    
                    if result.stdout:
                        execution_messages.append("Program output:")
                        execution_messages.append(result.stdout)
                        print("\nProgram output:")
                        print(result.stdout)
                    if result.stderr:
                        execution_messages.append("Program errors:")
                        execution_messages.append(result.stderr)
                        print("\nProgram errors:")
                        print(result.stderr)
                    
                    exit_msg = f"--- EXIT CODE {result.returncode} ---"
                    execution_messages.append(exit_msg)
                    print(f"\n{exit_msg}")
                    
                    # save log
                    log_to_file_only(sourceFile, "execution", execution_messages)
                    
                    if not generate_files:
                        c_path.unlink(missing_ok=True)
                                
                except FileNotFoundError:
                    error_msg = "\nWARNING: The 'gcc' command was not found."
                    compilation_messages.append(error_msg)
                    if generate_files:
                        file_msg = f"File C was indeed generated in: {c_path}"
                        compilation_messages.append(file_msg)
                    print(f"⚠ {error_msg}")
                    if generate_files:
                        print(f"  {file_msg}")
                    write_output_log(sourceFile, "compilation", compilation_messages, is_error=True)
                    
                except subprocess.CalledProcessError as e:
                    error_msg = f"\nERROR: GCC failed to compile the generated C file."
                    compilation_messages.append(error_msg)
                    compilation_messages.append(f"Error details: {e}")
                    if e.stderr:
                        compilation_messages.append(f"GCC stderr: {e.stderr}")
                    print(f"✗ {error_msg}")
                    print(f"  Error details: {e}")
                    if e.stderr:
                        print(f"  GCC stderr: {e.stderr}")
                    write_output_log(sourceFile, "compilation", compilation_messages, is_error=True)

            except SemanticError as e:
                error_messages = [
                    "--- SEMANTIC (SDT) ERROR ---",
                    "Parsing Success!",
                    f"SDT error: {e}"
                ]
                print(f"\n✗ SEMANTIC (SDT) ERROR")
                print(f"SDT error: {e}")
                write_output_log(sourceFile, "semantic", error_messages, is_error=True)
            
            except Exception as e:
                error_messages = [f"\nUnexpected error in code generation: {e}"]
                print(f"\n✗ Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                write_output_log(sourceFile, "codegen", error_messages, is_error=True)

if __name__ == "__main__":
    main()