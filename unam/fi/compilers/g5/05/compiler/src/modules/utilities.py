# modules/utilities.py (modificado)
from nltk import Tree as NLTKTree
from pathlib import Path
import re
import os

def get_project_root():
    # file inside src/ tree, return src's parent
    for ancestor in Path(__file__).resolve().parents:
        if ancestor.name == "src":
            return ancestor.parent

    # Fallback: search upwards for main.py or requirements.txt
    current_dir = Path(__file__).parent.resolve()
    while current_dir.parent != current_dir:
        if (current_dir / "main.py").exists() or (current_dir / "requirements.txt").exists():
            return current_dir
        current_dir = current_dir.parent
    return Path.cwd()  

def ensure_build_dir(source_file=None):
    """Create the build folder at project root (sibling to src and test)."""
    project_root = get_project_root()
    build_dir = project_root / "build"
    build_dir.mkdir(exist_ok=True)
    return build_dir

def get_output_filename(source_file):
    """ File name based in source file name"""
    source_path = Path(source_file)
    # If file is under tests/, use only the stem
    if "tests" in source_path.parts or "test" in source_path.parts:
        return source_path.stem
    # otherwise return path relative to project root, with separators replaced
    project_root = get_project_root()
    try:
        rel = source_path.relative_to(project_root)
        return str(rel).replace(os.sep, "_").replace(".", "_")
    except Exception:
        return source_path.stem

def tokens_to_file(category, token_count, source_file):
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    out_path = build_dir / f"{output_name}.txt"
    
    # Build token block
    token_lines = ["\n\n------------- TOKEN SUMMARY ------------\n"]
    for cat, values in category.items():
        unique_values = list(dict.fromkeys(values))
        token_lines.append(f"{cat.capitalize()} ({len(values)}): {' '.join(unique_values)}\n")
    token_lines.append(f"\nTotal tokens: {token_count}\n")
    token_block = "".join(token_lines)

    # Read existing content (if any) and remove previous TOKEN SUMMARY blocks
    existing = ""
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        pattern = r"\n\n------------- TOKEN SUMMARY ------------\n(?:.*?)(?=(\n\n------------- TOKEN SUMMARY ------------\n)|\Z)"
        existing = re.sub(pattern, "\n\n", existing, flags=re.DOTALL)

    # Insert token block at the start of file content
    new_content = token_block + existing

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\nTokens summary written to: {out_path}")
    return out_path

def to_nltk_tree(node):
    # If it's already an NLTK tree, return it
    if isinstance(node, NLTKTree):
        return node

    # If it's a string or terminal
    if isinstance(node, str):
        return node

    # If it's a tuple like ('Identifier', 'main')
    if isinstance(node, (tuple, list)) and len(node) == 2 and isinstance(node[0], str):
        return NLTKTree(node[0], [to_nltk_tree(node[1])])

    # If it has .children attribute (RPLY Tree)
    if hasattr(node, "children"):
        return NLTKTree(node.name, [to_nltk_tree(child) for child in node.children])

    # If it has .leaves() method (sometimes used)
    if hasattr(node, "leaves"):
        return NLTKTree(node.name, [to_nltk_tree(child) for child in node.leaves()])

    # Fallback — just make it a leaf
    return str(node)

def print_and_save_tree(parse_tree, source_file):
    """Pretty-print the parse tree and save it to the build/ file"""
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    out_path = build_dir / f"{output_name}.txt"

    nltk_tree = to_nltk_tree(parse_tree)

    # Read existing content (if any) and remove previous PARSE TREE blocks
    existing = ""
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        pattern = r"\n\n---------- PARSE TREE \(NTLK STYLE\) ----------\n(?:.*?)(?=(\n\n---------- PARSE TREE \(NTLK STYLE\) ----------\n)|\Z)"
        existing = re.sub(pattern, "\n\n", existing, flags=re.DOTALL)

    # Write back the cleaned content and append the single new parse-tree block
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(existing)
        f.write("\n\n---------- PARSE TREE (NTLK STYLE) ----------\n")
        f.write(nltk_tree.pformat())
    print(f"\nParse tree written to: {out_path}")

def write_tac(tac_lines, source_file):
    """Write TAC block to build/ file"""
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    out_path = build_dir / f"{output_name}.txt"

    existing = ""
    if out_path.exists():
        existing = out_path.read_text(encoding="utf-8")
        # Remove previous TAC blocks marked by the header
        pattern = r"\n\n--------- THREE ADDRESS CODE \(TAC\): --------\n(?:.*?)(?=(\n\n------------- THREE ADDRESS CODE \(TAC\): ------------\n)|\Z)"
        existing = re.sub(pattern, "\n\n", existing, flags=re.DOTALL)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(existing)
        f.write("\n\n--------- THREE ADDRESS CODE (TAC): --------\n")
        for line in tac_lines:
            f.write(line + "\n")
    #print(f"\nTAC written to: {out_path}")

def write_output_log(source_file, phase, messages, is_error=False, clear_first=False):
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    log_path = build_dir / f"{output_name}.log"
    
    mode = "a" if log_path.exists() else "w"
    
    with open(log_path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("=" * 60 + "\n")
            f.write("COMPILER OUTPUT LOG\n")
            f.write("=" * 60 + "\n\n")
        
        f.write(f"\n{'='*40}\n")
        if is_error:
            f.write(f"PHASE: {phase.upper()} - ERROR\n")
        else:
            f.write(f"PHASE: {phase.upper()}\n")
        f.write(f"{'='*40}\n")
        
        for msg in messages:
            f.write(f"{msg}\n")
    
    return log_path

def write_semantic_debug(source_file, symbol_table_info, semantic_events):
    """Escribe información de debug del análisis semántico (opcional, solo si --debug flag)"""
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    debug_path = build_dir / f"{output_name}_semantic_debug.txt"
    
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("SEMANTIC DEBUG INFORMATION\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("SYMBOL TABLE:\n")
        f.write("-" * 40 + "\n")
        f.write(symbol_table_info + "\n\n")
        
        f.write("SEMANTIC EVENTS:\n")
        f.write("-" * 40 + "\n")
        for event in semantic_events:
            f.write(f"{event}\n")
    
    print(f"\nSemantic debug info written to: {debug_path}")
    return debug_path


def write_log_entry(source_file, phase, messages, is_error=False):
    """Write a single log entry to the .log file without printing to console."""
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    log_path = build_dir / f"{output_name}.log"
    
    mode = "a" if log_path.exists() else "w"
    
    with open(log_path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("=" * 60 + "\n")
            f.write("COMPILER OUTPUT LOG\n")
            f.write("=" * 60 + "\n\n")
        
        f.write(f"\n{'='*40}\n")
        if is_error:
            f.write(f"PHASE: {phase.upper()} - ERROR\n")
        else:
            f.write(f"PHASE: {phase.upper()}\n")
        f.write(f"{'='*40}\n")
        
        for msg in messages:
            f.write(f"{msg}\n")
    
    return log_path

def log_to_file_only(source_file, phase, messages, is_error=False, clear_first=False):
    """Log to file only - for detailed logging (no console output)."""
    build_dir = ensure_build_dir()
    output_name = get_output_filename(source_file)
    log_path = build_dir / f"{output_name}.log"
    
    # Handle clear_first
    if clear_first and log_path.exists():
        log_path.unlink()
    
    mode = "a" if log_path.exists() else "w"
    
    with open(log_path, mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("=" * 60 + "\n")
            f.write("COMPILER OUTPUT LOG\n")
            f.write("=" * 60 + "\n\n")
        
        f.write(f"\n{'='*40}\n")
        if is_error:
            f.write(f"PHASE: {phase.upper()} - ERROR\n")
        else:
            f.write(f"PHASE: {phase.upper()}\n")
        f.write(f"{'='*40}\n")
        
        for msg in messages:
            f.write(f"{msg}\n")
    
    return log_path


# For important phases that need console feedback:
def log_with_console(source_file, phase, messages, is_error=False):
    """Log to file AND show important messages on console."""
    # First log to file
    log_path = write_log_entry(source_file, phase, messages, is_error)
    
    # Show only key messages on console
    if is_error:
        print(f"\n--- {phase.upper()} ERROR ---")
        for msg in messages[-3:]:  # Show last 3 messages
            print(f"  {msg}")
    else:
        print(f"\n{phase.capitalize()} phase completed")
        # Show success message if present
        for msg in messages:
            if "success" in msg.lower() or "verified" in msg.lower():
                print(f"  {msg}")
    
    return log_path