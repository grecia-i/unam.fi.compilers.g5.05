from rply import LexerGenerator

class Lexer():
    def __init__(self) -> None:
        self.lexer = LexerGenerator()

    def _add_tokens(self):
        #self.lexer.add('NOMBRE_DEL_TOKEN', r'EXPRESION_REGULAR_PARA_IDENTIFICARLO')
        #self.lexer.add()

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
        self.lexer.add("KW_FUNC",           r"\bfunc\b")

        # --- TYPES ---
        self.lexer.add("TYPE_INT",          r'int')
        self.lexer.add("TYPE_FLOAT32",      r'float32')
        self.lexer.add("TYPE_FLOAT32",      r'float64')
        self.lexer.add("TYPE_BOOL",         r'bool')
        self.lexer.add("TYPE_STR",          r'string')

        # --- Literals ---
        self.lexer.add('LIT_FLOAT',         r'-?\d+\.\d+')
        self.lexer.add('LIT_INT',           r'-?\d+')
        self.lexer.add('LIT_STR',           r'"(\\.|[^"\\])*"')
        self.lexer.add('LIT_BOOL',          r'Verdadero|Falso')

        # --- Operators ---
        self.lexer.add("OP_PLUSEQ",         r"\+=")
        self.lexer.add("OP_PLUSPLUS",       r"\+\+")
        self.lexer.add("OP_MINUSEQ",        r"-=")
        self.lexer.add("OP_MINUSMINUS",     r"--")
        self.lexer.add("OP_LEFTARROW",      r"<-")
        self.lexer.add("OP_MULEQ",          r"\*=")
        self.lexer.add("OP_DIVEQ",          r"/=")
        self.lexer.add("OP_MODEQ",          r"%=")
        self.lexer.add("OP_ANDEQ",          r"&=")
        self.lexer.add("OP_ANDAND",         r"&&")
        self.lexer.add("OP_ANDNOTEQ",       r"&\^=")
        self.lexer.add("OP_ANDNOT",         r"&\^")
        self.lexer.add("OP_OREQ",           r"\|=")
        self.lexer.add("OP_OROR",           r"\|\|")
        self.lexer.add("OP_XOREQ",          r"\^=")
        self.lexer.add("OP_SHLEQ",          r"<<=")
        self.lexer.add("OP_SHREQ",          r">>=")
        self.lexer.add("OP_EQEQ",           r"==")
        self.lexer.add("OP_NEQ",            r"!=")
        self.lexer.add("OP_LTE",            r"<=")
        self.lexer.add("OP_GTE",            r">=")
        self.lexer.add("OP_COLONEQ",        r":=")
        self.lexer.add("OP_DOTDOTDOT",      r"\.\.\.")

        self.lexer.add("OP_PLUS",           r"\+")
        self.lexer.add("OP_MINUS",          r"-")
        self.lexer.add("OP_MUL",            r"\*")
        self.lexer.add("OP_DIV",            r"/")
        self.lexer.add("OP_MOD",            r"%")
        self.lexer.add("OP_AND",            r"&")
        self.lexer.add("OP_OR",             r"\|")
        self.lexer.add("OP_XOR",            r"\^")
        self.lexer.add("OP_SHL",            r"<<")
        self.lexer.add("OP_SHR",            r">>")
        self.lexer.add("OP_EQ",             r"=")
        self.lexer.add("OP_LT",             r"<")
        self.lexer.add("OP_GT",             r">")
        self.lexer.add("OP_NOT",            r"!")
        self.lexer.add("OP_TILDE",          r"~")
        self.lexer.add("OP_DOT",            r"\.")

        # --- Punctuation ---
        self.lexer.add("PUNC_LPAREN",       r"\(")
        self.lexer.add("PUNC_RPAREN",       r"\)")
        self.lexer.add("PUNC_LBRACK",       r"\[")
        self.lexer.add("PUNC_RBRACK",       r"\]")
        self.lexer.add("PUNC_LBRACE",       r"\{")
        self.lexer.add("PUNC_RBRACE",       r"\}")
        self.lexer.add("PUNC_COMMA",        r",")
        self.lexer.add("PUNC_SEMI",         r";")
        self.lexer.add("PUNC_COLON",        r":")

        self.lexer.add('IDENT',             r'[A-Za-z][A-Za-z0-9_]*')

        self.lexer.ignore(r"//[^\n]*")
        self.lexer.ignore(r"\s+")


    def get_lexer(self):
        self._add_tokens()
        return self.lexer.build()