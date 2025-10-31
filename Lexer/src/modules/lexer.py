from rply import LexerGenerator, errors
from collections import defaultdict


class Lexer:
    def __init__(self) -> None:
        self.lexer = LexerGenerator()
        self.category = defaultdict(list)
        self.token_count = 0
        self._add_tokens()

    def _add_tokens(self):
        # self.lexer.add('NOMBRE_DEL_TOKEN', r'EXPRESION_REGULAR_PARA_IDENTIFICARLO')
        # self.lexer.add()

        # --- Keywords ---
        self.lexer.add("KW_BREAK",          r"\bbreak\b")
        self.lexer.add("KW_DEFAULT",        r"\bdefault\b")
        self.lexer.add("KW_FUNC",           r"\bfunc\b")
        self.lexer.add("KW_INTERFACE",      r"\binterface\b")
        self.lexer.add("KW_SELECT",         r"\bselect\b")
        self.lexer.add("KW_CASE",           r"\bcase\b")
        self.lexer.add("KW_DEFER",          r"\bdefer\b")
        self.lexer.add("KW_GO",             r"\bgo\b")
        self.lexer.add("KW_MAP",            r"\bmap\b")
        self.lexer.add("KW_STRUCT",         r"\bstruct\b")
        self.lexer.add("KW_CHAN",           r"\bchan\b")
        self.lexer.add("KW_ELSE",           r"\belse\b")
        self.lexer.add("KW_GOTO",           r"\bgoto\b")
        self.lexer.add("KW_PACKAGE",        r"\bpackage\b")
        self.lexer.add("KW_SWITCH",         r"\bswitch\b")
        self.lexer.add("KW_CONST",          r"\bconst\b")
        self.lexer.add("KW_FALLTHROUGH",    r"\bfallthrough\b")
        self.lexer.add("KW_IF",             r"\bif\b")
        self.lexer.add("KW_RANGE",          r"\brange\b")
        self.lexer.add("KW_TYPE",           r"\btype\b")
        self.lexer.add("KW_CONTINUE",       r"\bcontinue\b")
        self.lexer.add("KW_FOR",            r"\bfor\b")
        self.lexer.add("KW_IMPORT",         r"\bimport\b")
        self.lexer.add("KW_RETURN",         r"\breturn\b")
        self.lexer.add("KW_VAR",            r"\bvar\b")

        # --- TYPES ---
        self.lexer.add("TYPE_INT", r"int")
        self.lexer.add("TYPE_FLOAT32", r"float32")
        self.lexer.add("TYPE_FLOAT32", r"float64")
        self.lexer.add("TYPE_BOOL", r"bool")
        self.lexer.add("TYPE_STR", r"string")

        # --- Literals ---
        self.lexer.add("LIT_FLOAT", r"-?\d+\.\d+")
        self.lexer.add("LIT_INT", r"-?\d+")
        self.lexer.add("LIT_STR", r'"(\\.|[^"\\])*"')
        self.lexer.add("LIT_BOOL", r"true|false")

        # --- Operators ---
        self.lexer.add("OP_PLUSEQ", r"\+=")
        self.lexer.add("OP_PLUSPLUS", r"\+\+")
        self.lexer.add("OP_MINUSEQ", r"-=")
        self.lexer.add("OP_MINUSMINUS", r"--")
        self.lexer.add("OP_LEFTARROW", r"<-")
        self.lexer.add("OP_MULEQ", r"\*=")
        self.lexer.add("OP_DIVEQ", r"/=")
        self.lexer.add("OP_MODEQ", r"%=")
        self.lexer.add("OP_ANDEQ", r"&=")
        self.lexer.add("OP_ANDAND", r"&&")
        self.lexer.add("OP_ANDNOTEQ", r"&\^=")
        self.lexer.add("OP_ANDNOT", r"&\^")
        self.lexer.add("OP_OREQ", r"\|=")
        self.lexer.add("OP_OROR", r"\|\|")
        self.lexer.add("OP_XOREQ", r"\^=")
        self.lexer.add("OP_SHLEQ", r"<<=")
        self.lexer.add("OP_SHREQ", r">>=")
        self.lexer.add("OP_EQEQ", r"==")
        self.lexer.add("OP_NEQ", r"!=")
        self.lexer.add("OP_LTE", r"<=")
        self.lexer.add("OP_GTE", r">=")
        self.lexer.add("OP_COLONEQ", r":=")
        self.lexer.add("OP_DOTDOTDOT", r"\.\.\.")

        self.lexer.add("OP_PLUS", r"\+")
        self.lexer.add("OP_MINUS", r"-")
        self.lexer.add("OP_MUL", r"\*")
        self.lexer.add("OP_DIV", r"/")
        self.lexer.add("OP_MOD", r"%")
        self.lexer.add("OP_AND", r"&")
        self.lexer.add("OP_OR", r"\|")
        self.lexer.add("OP_XOR", r"\^")
        self.lexer.add("OP_SHL", r"<<")
        self.lexer.add("OP_SHR", r">>")
        self.lexer.add("OP_EQ", r"=")
        self.lexer.add("OP_LT", r"<")
        self.lexer.add("OP_GT", r">")
        self.lexer.add("OP_NOT", r"!")
        self.lexer.add("OP_TILDE", r"~")
        self.lexer.add("OP_DOT", r"\.")

        # --- Punctuation ---
        self.lexer.add("PUNC_LPAREN", r"\(")
        self.lexer.add("PUNC_RPAREN", r"\)")
        self.lexer.add("PUNC_LBRACK", r"\[")
        self.lexer.add("PUNC_RBRACK", r"\]")
        self.lexer.add("PUNC_LBRACE", r"\{")
        self.lexer.add("PUNC_RBRACE", r"\}")
        self.lexer.add("PUNC_COMMA", r",")
        self.lexer.add("PUNC_SEMI", r";")
        self.lexer.add("PUNC_COLON", r":")

        self.lexer.add("IDENT", r"[A-Za-z][A-Za-z0-9_]*")

        # --- Comments ---
        self.lexer.ignore(r"//[^\n]*")
        self.lexer.ignore(r"/\*[\s\S]*?\*/")
        self.lexer.ignore(r"\s+")

    def categorize_token(self, token):
        self.token_count += 1
        name = token.name
        value = token.value

        if name.startswith("KW_"):
            self.category["keywords"].append(value)

        elif name.startswith("TYPE_"):
            self.category["types"].append(value)

        elif (
            name.startswith("LIT_INT")
            or name.startswith("LIT_FLOAT")
            or name.startswith("LIT_BOOL")
        ):
            self.category["numbers"].append(value)

        elif name.startswith("LIT_STR"):
            self.category["strings"].append(value)

        elif name == "IDENT":
            self.category["identifiers"].append(value)

        elif name.startswith("OP_"):
            self.category["operators"].append(value)

        elif name.startswith("PUNC_"):
            self.category["delimiters"].append(value)
        else:
            self.category["others"].append(value)

    def summary(self):
        print("\n---------- TOKEN SUMMARY ----------")
        for category, values in self.category.items():
            unique_values = list(dict.fromkeys(values))
            total = len(values)
            print(f"{category.capitalize()} ({total}): {' '.join(unique_values)}")
        print(f"\nTotal tokens: {self.token_count}")

    def save_tokens_to_file(self, filename="tokens.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            for category, values in self.category.items():
                f.write(
                    f"{category.capitalize()} ({len(values)}): {' '.join(values)}\n"
                )
            f.write(f"\nTotal tokens: {self.token_count}\n")

    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()
