from nltk import Tree as NLTKTree
from pathlib import Path


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
    """Pretty-print the parse tree and save it to <source_file>.tree.txt."""
    nltk_tree = to_nltk_tree(parse_tree)

    print("\n---------- PARSE TREE (NTLK STYLE) ----------")
    nltk_tree.pretty_print()

    # Save to file
    project_root = Path(__file__).parent.resolve()
    out_path = project_root / f"{Path(source_file).stem}.tree.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(nltk_tree.pformat())
    print(f"\nParse tree saved to: {out_path}")
