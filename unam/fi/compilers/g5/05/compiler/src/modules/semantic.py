## --- semantic.py ---

from nltk.tree import Tree

class SemanticError(Exception):
    """Custom exeption for semantic errors (SDT)."""
    pass

# 2. Define the Symbol Table (handles scopes)
class SymbolTable:
    def __init__(self):
        # A stack of dictionaries. The last one is the current scope.
        self.stack = [{}] # Global scope

    def enter_scope(self):
        """Pushes a new scope (dictionary) onto the stack."""
        self.stack.append({})
        print(f"[SymbolTable] > Entering new scope (level {len(self.stack)})")

    def exit_scope(self):
        """Pops the current scope from the stack."""
        if len(self.stack) > 1:
            self.stack.pop()
            print(f"[SymbolTable] < Exiting scope (returning to level {len(self.stack)})")

    def add_symbol(self, name, symbol_type_tree):
        """Adds a symbol (variable) to the current scope."""
        current_scope = self.stack[-1]
        type_name = symbol_type_tree 
        if name in current_scope:
            raise SemanticError(f"SDT Error: Variable '{name}' already declared in this scope.")
        
        current_scope[name] = type_name[0]
        print(f"[SymbolTable] Declared '{name}' as '{type_name}'")

    def lookup_symbol(self, name):
        """Finds a symbol (variable) by searching all scopes."""
        # Search from the innermost scope to the outermost
        for scope in reversed(self.stack):
            if name in scope:
                return scope[name] # Returns the type ('int', 'string')
        
        raise SemanticError(f"SDT Error: Undeclared variable '{name}'.")

# Define the Semantic Analyzer (The "Visitor")
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def visit(self, node):
        """Main dispatch function for the visitor pattern."""
        if not isinstance(node, Tree):
            return
            
        node_label = node.label()
        method_name = f'visit_{node_label}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node):
        """Generic visit method: just visits all children."""
        for child in node:
            self.visit(child)
            

    def visit_Block(self, node):
        """SDT Rule: Entering a block creates a new scope."""
        self.symbol_table.enter_scope()
        self.generic_visit(node) 
        self.symbol_table.exit_scope()

    def visit_VarDecl(self, node):
        """SDT Rule: Process a variable declaration."""
        for var_spec in node[0]:
            self.visit(var_spec) # Call visit_VarSpec
    
    def visit_Parameters(self, node):
        for param_decl_node in node:  # puede haber varios ParameterDecl
            self.visit(param_decl_node)
    
    def visit_ParameterDecl(self, node):
        """
        SDT Rule: Treat a function parameter as VarSpec
        """
        ident_node = node[0]   # Identifier
        type_node = node[1]    # SimpleType
        var_name = ident_node[0]       # "n"
        var_type_tree = type_node    # Tree("SimpleType", ["int"])

        # Agregar a la tabla como VarSpec
        self.symbol_table.add_symbol(var_name, var_type_tree)

        print(f"[Semantic] Parameter '{var_name}' declared with type '{var_type_tree}'")
    
    def visit_path(self, node):
        """
        SDT Rule: Treat a function parameter as VarSpec
        """
        
        ident_node = node  # Identifier
        type_node = Tree("SimpleType", ["int"])    # SimpleType

        var_name = ident_node[0]       # "n"
        var_type_tree = type_node    # Tree("SimpleType", ["int"])

        # Agregar a la tabla como VarSpec
        self.symbol_table.add_symbol(var_name, var_type_tree)

        print(f"[Semantic] Parameter '{var_name}' declared with type '{var_type_tree}'")

    def visit_VarSpec(self, node):
        """SDT Rule: Add declared variables to the symbol table."""
        ident_list_node = node[0]
        type_node = node[1]
        expr_list_node = node[2]

        if len(type_node) == 0:
            print("WARNING: Type inference is not implemented.")
            return
        
        var_type_tree = type_node
        
        for ident_node in ident_list_node:
            var_name = ident_node[0] 
            self.symbol_table.add_symbol(var_name, var_type_tree)

    def visit_AssignStmt(self, node):
        """SDT Rule: On assignment, check types."""
        left_expr_list = node[0]
        right_expr_list = node[2]
        
        if len(left_expr_list) == 1 and len(right_expr_list) == 1:
            left_expr = left_expr_list[0]
            right_expr = right_expr_list[0]
            
            var_name = None
            if isinstance(left_expr, Tree) and left_expr.label() == 'Identifier':
                var_name = left_expr[0]
            
            elif hasattr(left_expr, 'gettokentype') and left_expr.gettokentype() == 'IDENT':
                 var_name = left_expr.getstr()

            if var_name:
                # 1. Check if variable exists (SDT)
                var_type = self.symbol_table.lookup_symbol(var_name)
                
                # 2. Get the expression's type (by visiting the child)
                expr_type = self.visit(right_expr) 
                
                # 3. Compare types (SDT)
                if var_type != expr_type:
                    raise SemanticError(f"SDT Error: Cannot assign type '{expr_type}' to variable '{var_name}' of type '{var_type}'")
                print(f"[Semantic] Assignment to '{var_name}' OK (type {var_type})")
            else:
                raise SemanticError("SDT Error: Left side of an assignment must be a variable.")
            
    def visit_FunctionDecl(self, node):
        """
        SDT Rule: Add function to parent scope, then visit its block.
        """
        func_name_node = node[0]
        func_name = func_name_node[0]
        
        self.symbol_table.add_symbol(func_name, Tree("SimpleType", ["function"]))
        
        self.symbol_table.enter_scope()

        parameters_node = node[1]  # Parameters node
        if parameters_node:
            self.visit(parameters_node)  # Llamará a visit_Parameters -> visit_ParameterDecl
    
        block_node = node[2]
        self.visit(block_node)
        
    def visit_ShortVarDecl(self, node):
        """
        SDT Rule: Handles short variable declaration (:=)
        """
        if len(node) == 1 and node[0].label() == 'ShortVarDecl':
            # Si es así, solo visitamos al hijo y terminamos
            self.visit(node[0])
            return

        ident_list_node = node[0]
        expr_list_node = node[1]
        
        if len(ident_list_node) == 1 and len(expr_list_node) == 1:
            var_name = ident_list_node[0][0] # IdentList -> Ident -> "a"
            expr_type = self.visit(expr_list_node[0])
            
            fake_type_tree = Tree("SimpleType", [expr_type])
            self.symbol_table.add_symbol(var_name, fake_type_tree)
            
            print(f"[Semantic] Short declaration of '{var_name}' as '{expr_type}' OK")
        else:
            print("WARNING: Multiple assignment for ':=' not implemented.")

    def visit_BinaryExpr(self, node):
        """SDT Rule: In binary operation, check types and return result type."""
        left_type = self.visit(node[0])
        right_type = self.visit(node[2])
        
        if left_type != 'int' or right_type != 'int':
            op = node[1][0] 
            raise SemanticError(f"SDT Error: Operation '{op}' only supports 'int' with 'int', not '{left_type}' with '{right_type}'")
        
        return 'int'

    def visit_PackageClause(self, node):
        """
        SDT Rule: Handles the 'package' clause.
        We don't need to do anything with the package name,
        so we just pass. Crucially, we DON'T call generic_visit.
        """
        # No hacemos nada. No visitamos a los hijos (como Identifier("main"))
        pass

    def visit_Identifier(self, node):
        """SDT Rule: When using a variable, look it up and return its type."""
        var_name = node[0]
        var_type = self.symbol_table.lookup_symbol(var_name)
        
        return var_type 

    def visit_IntLiteral(self, node):
        return 'int'

    def visit_StringLiteral(self, node):
        return 'string'
        
    def visit_FloatLiteral(self, node):
        return 'float64' 
        
    def visit_BoolLiteral(self, node):
        return 'bool'
    
    def visit_QualifiedIdent(self, node):
        """
        SDT Rule: Treat a function parameter as VarSpec
        """
        print("************************")
        right_type = self.visit(node[0])
        ident_node = node[1]  # Identifier
        type_node = Tree("SimpleType", ["int"])    # SimpleType

        var_name = ident_node[0]       # "n"
        var_type_tree = type_node    # Tree("SimpleType", ["int"])
        
        # Agregar a la tabla como VarSpec
        self.symbol_table.add_symbol(var_name, var_type_tree)
        right_type = self.visit(node[1])
        print(f"[Semantic] Parameter '{var_name}' declared with type '{var_type_tree}'")
    