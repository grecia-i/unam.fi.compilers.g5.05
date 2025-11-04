from nltk import Tree as NLTKTree
from pathlib import Path

def tokens_to_file(category, token_count, filename="tokens.txt"):
    out_path = Path(filename)

    # If the passed path has no parent or parent doesn't exist, fallback to project root
    if not out_path.parent.exists():
        fallback = Path(__file__).parent.parent.resolve()
        out_path = fallback / out_path.name

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n------------- TOKEN SUMMARY ------------\n")
        for cat, values in category.items():
            unique_values = list(dict.fromkeys(values))
            f.write(f"{cat.capitalize()} ({len(values)}): {' '.join(unique_values)}\n")
        f.write(f"\nTotal tokens: {token_count}\n")
    print(f"\nTokens summary written to: {out_path}")

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
    """Pretty-print the parse tree and save it to the provided file (appended)."""
    nltk_tree = to_nltk_tree(parse_tree)
    out_path = Path(source_file)

    # If the passed path has no parent or parent doesn't exist, fallback to modules parent.
    if not out_path.parent.exists():
        fallback = Path(__file__).parent.parent.resolve()
        out_path = fallback / out_path.name

    with open(out_path, "a", encoding="utf-8") as f:
        f.write("\n\n---------- PARSE TREE (NTLK STYLE) ----------\n")
        f.write(nltk_tree.pformat())
    print(f"\nParse tree appended to: {out_path}")
