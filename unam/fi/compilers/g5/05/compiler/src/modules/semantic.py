# --- semantic.py ---

from nltk.tree import Tree

class SemanticError(Exception):
    """Custom exception for semantic errors (SDT)."""
    pass

# 2. Define the Symbol Table (handles scopes)
class SymbolTable:
    def __init__(self, printer=None):
        # A stack of dictionaries. The last one is the current scope.
        self.stack = [{}] # Global scope
        self.scope_level = 0
        self.printer = printer or (lambda msg: None)

    def enter_scope(self):
        """Pushes a new scope (dictionary) onto the stack."""
        self.stack.append({})
        self.scope_level += 1
        self.printer(f"[SymbolTable] > Entering new scope (level {self.scope_level})")

    def exit_scope(self):
        """Pops the current scope from the stack."""
        if len(self.stack) > 1:
            self.stack.pop()
            self.scope_level -= 1
            self.printer(f"[SymbolTable] < Exiting scope (returning to level {self.scope_level})")

    def add_symbol(self, name, symbol_type_tree):
        """Adds a symbol (variable) to the current scope."""
        current_scope = self.stack[-1]
        type_name = symbol_type_tree 
        if name in current_scope:
            raise SemanticError(f"SDT Error: Variable '{name}' already declared in this scope.")
        
        current_scope[name] = type_name[0] if isinstance(type_name, Tree) and len(type_name) > 0 else str(type_name)
        self.printer(f"[SymbolTable] Declared '{name}' as '{type_name}'")

    def lookup_symbol(self, name):
        """Finds a symbol (variable) by searching all scopes."""
        # Search from the innermost scope to the outermost
        for i in range(len(self.stack)-1, -1, -1):
            scope = self.stack[i]
            if name in scope:
                self.printer(f"[SymbolTable] Found '{name}' in scope level {i}")
                return scope[name] # Returns the type ('int', 'string')
        
        raise SemanticError(f"SDT Error: Undeclared variable '{name}'.")
    
    def get_info(self):
        """Obtiene información de la tabla de símbolos como string"""
        info = f"Symbol Table (Current scope level: {self.scope_level})\n"
        info += "=" * 50 + "\n"
        
        for i, scope in enumerate(self.stack):
            info += f"\nScope Level {i}:\n"
            info += "-" * 20 + "\n"
            if scope:
                for name, symbol_type in scope.items():
                    info += f"  {name}: {symbol_type}\n"
            else:
                info += "  (empty)\n"
        
        return info

# Define the Semantic Analyzer (The "Visitor")
class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.output_messages = []  # Mensajes de output importantes
        self.debug_messages = []   # Mensajes de debug (solo con --debug)
        self.debug_mode = False
        # When False, messages are recorded but not printed (useful to keep logs but avoid console spam).
        self.echo_output = False
        self.semantic_events = []  # Eventos semánticos (declaraciones, usos, etc.)
        self.symbol_table = SymbolTable(printer=self._print_if_enabled)

    def _print_if_enabled(self, msg):
        if self.echo_output:
            print(msg)
    
    def set_debug_mode(self, enabled):
        """Activa o desactiva modo debug"""
        self.debug_mode = enabled
    
    def set_echo_output(self, enabled):
        """Enable/disable printing of semantic output messages to stdout.
        When disabled, messages are still recorded and can be written to log files.
        """
        self.echo_output = enabled
    
    def log_output(self, message):
        """Registra un mensaje de output importante"""
        self.output_messages.append(message)
        if self.echo_output:
            self.printer(f"[SEMANTIC] {message}")
    
    def log_debug(self, message):
        """Registra un mensaje de debug (solo en modo debug)"""
        if self.debug_mode:
            self.debug_messages.append(message)
            if self.echo_output:
                self.printer(f"[SEMANTIC DEBUG] {message}")
    
    def log_event(self, event_type, details):
        """Registra un evento semántico"""
        event = f"{event_type}: {details}"
        self.semantic_events.append(event)
        self.log_debug(event)
    
    def get_output_messages(self):
        """Obtiene los mensajes de output"""
        return self.output_messages.copy()
    
    def get_debug_info(self):
        """Obtiene información de debug"""
        return {
            'output_messages': self.output_messages,
            'debug_messages': self.debug_messages,
            'semantic_events': self.semantic_events
        }
    
    def get_symbol_table_info(self):
        """Obtiene información de la tabla de símbolos como string"""
        return self.symbol_table.get_info()
    
    def get_semantic_events(self):
        """Obtiene la lista de eventos semánticos"""
        return self.semantic_events.copy()

    def visit(self, node):
        """Main dispatch function for the visitor pattern."""
        if not isinstance(node, Tree):
            return
            
        node_label = node.label()
        method_name = f'visit_{node_label}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        
        self.log_event(f"VISIT_{node_label.upper()}", f"Entering {node_label} node")
        result = visitor_method(node)
        self.log_event(f"EXIT_{node_label.upper()}", f"Exiting {node_label} node")
        
        return result

    def generic_visit(self, node):
        """Generic visit method: just visits all children."""
        self.log_debug(f"Generic visit for node type: {node.label() if isinstance(node, Tree) else type(node).__name__}")
        for child in node:
            self.visit(child)

    def visit_Block(self, node):
        """SDT Rule: Entering a block creates a new scope."""
        self.log_output(f"Entering block (new scope)")
        self.log_event("SCOPE_ENTER", "Block scope")
        self.symbol_table.enter_scope()
        self.generic_visit(node)
        self.log_output(f"Exiting block (scope closed)")
        self.log_event("SCOPE_EXIT", "Block scope")
        self.symbol_table.exit_scope()

    def visit_VarDecl(self, node):
        """SDT Rule: Process a variable declaration."""
        self.log_output(f"Processing variable declaration")
        self.log_event("VAR_DECL_START", "Variable declaration block")
        for var_spec in node[0]:
            self.visit(var_spec)  # Call visit_VarSpec
        self.log_event("VAR_DECL_END", "Variable declaration block completed")

    def visit_Parameters(self, node):
        self.log_output(f"Processing function parameters")
        self.log_event("PARAMETERS_START", "Function parameters")
        for param_decl_node in node:  # puede haber varios ParameterDecl
            self.visit(param_decl_node)
        self.log_event("PARAMETERS_END", f"{len(node)} parameter(s) processed")

    def visit_ParameterDecl(self, node):
        """SDT Rule: Treat a function parameter as VarSpec"""
        ident_node = node[0]   # Identifier
        type_node = node[1]    # SimpleType
        var_name = ident_node[0]       # "n"
        var_type = type_node[0] if isinstance(type_node, Tree) and len(type_node) > 0 else str(type_node)

        # Agregar a la tabla como VarSpec
        self.symbol_table.add_symbol(var_name, type_node)
        
        self.log_output(f"Parameter '{var_name}' declared with type '{var_type}'")
        self.log_event("PARAMETER_DECL", f"'{var_name}' as {var_type}")

    def visit_path(self, node):
        """SDT Rule: Treat a function parameter as VarSpec"""
        self.log_debug(f"Processing path node: {node}")
        ident_node = node  # Identifier
        type_node = Tree("SimpleType", ["int"])

        var_name = ident_node[0]       # "n"
        var_type_tree = type_node

        # Agregar a la tabla como VarSpec
        self.symbol_table.add_symbol(var_name, var_type_tree)
        
        self.log_output(f"Path parameter '{var_name}' declared with type 'int'")
        self.log_event("PATH_PARAMETER", f"'{var_name}' as int")

    def visit_VarSpec(self, node):
        """SDT Rule: Add declared variables to the symbol table."""
        ident_list_node = node[0]
        type_node = node[1]
        expr_list_node = node[2] if len(node) > 2 else None

        if len(type_node) == 0:
            warning_msg = "WARNING: Type inference is not implemented."
            self.log_output(warning_msg)
            self.log_event("TYPE_INFERENCE_WARNING", "Type inference not implemented")
            return
        
        var_type = type_node[0] if isinstance(type_node, Tree) and len(type_node) > 0 else str(type_node)
        
        variable_count = 0
        for ident_node in ident_list_node:
            var_name = ident_node[0] 
            self.symbol_table.add_symbol(var_name, type_node)
            self.log_output(f"Variable '{var_name}' declared with type '{var_type}'")
            self.log_event("VARIABLE_DECL", f"'{var_name}' as {var_type}")
            variable_count += 1
        
        self.log_output(f"Declared {variable_count} variable(s) with type '{var_type}'")

    def visit_AssignStmt(self, node):
        """SDT Rule: On assignment, check types."""
        self.log_output(f"Processing assignment statement")
        self.log_event("ASSIGNMENT_START", "Assignment statement")
        
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
                self.log_output(f"Variable '{var_name}' found with type '{var_type}'")
                
                # 2. Get the expression's type (by visiting the child)
                expr_type = self.visit(right_expr)
                self.log_output(f"Right expression evaluated to type '{expr_type}'")
                
                # 3. Compare types (SDT)
                if var_type != expr_type:
                    error_msg = f"SDT Error: Cannot assign type '{expr_type}' to variable '{var_name}' of type '{var_type}'"
                    self.log_output(error_msg)
                    self.log_event("TYPE_MISMATCH_ERROR", error_msg)
                    raise SemanticError(error_msg)
                
                success_msg = f"Assignment to '{var_name}' OK (type {var_type})"
                self.log_output(success_msg)
                self.log_event("ASSIGNMENT_OK", success_msg)
            else:
                error_msg = "SDT Error: Left side of an assignment must be a variable."
                self.log_output(error_msg)
                self.log_event("ASSIGNMENT_ERROR", error_msg)
                raise SemanticError(error_msg)
        else:
            warning_msg = "WARNING: Multiple assignment not fully implemented."
            self.log_output(warning_msg)
            self.log_event("MULTIPLE_ASSIGNMENT_WARNING", warning_msg)

    def visit_FunctionDecl(self, node):
        """SDT Rule: Add function to parent scope, then visit its block."""
        func_name_node = node[0]
        func_name = func_name_node[0]
        
        self.log_output(f"Processing function declaration: {func_name}")
        self.log_event("FUNCTION_DECL_START", f"Function '{func_name}'")
        
        # Add function to symbol table
        self.symbol_table.add_symbol(func_name, Tree("SimpleType", ["function"]))
        self.log_output(f"Function '{func_name}' added to symbol table")
        
        # Enter function scope
        self.symbol_table.enter_scope()
        self.log_output(f"Entering function scope for '{func_name}'")

        parameters_node = node[1]  # Parameters node
        if parameters_node:
            self.log_output(f"Processing parameters for function '{func_name}'")
            self.visit(parameters_node)  # Llamará a visit_Parameters -> visit_ParameterDecl

        block_node = node[2]
        self.log_output(f"Processing function body for '{func_name}'")
        self.visit(block_node)
        
        self.log_output(f"Exiting function scope for '{func_name}'")
        self.symbol_table.exit_scope()
        
        self.log_output(f"Function '{func_name}' declaration completed")
        self.log_event("FUNCTION_DECL_END", f"Function '{func_name}'")

    def visit_ShortVarDecl(self, node):
        """SDT Rule: Handles short variable declaration (:=)"""
        self.log_output(f"Processing short variable declaration")
        self.log_event("SHORT_VAR_DECL_START", "Short declaration (:=)")
        
        if len(node) == 1 and node[0].label() == 'ShortVarDecl':
            # Si es así, solo visitamos al hijo y terminamos
            self.log_debug(f"Nested ShortVarDecl detected")
            self.visit(node[0])
            return

        ident_list_node = node[0]
        expr_list_node = node[1]
        
        if len(ident_list_node) == 1 and len(expr_list_node) == 1:
            var_name = ident_list_node[0][0]  # IdentList -> Ident -> "a"
            expr_type = self.visit(expr_list_node[0])
            
            fake_type_tree = Tree("SimpleType", [expr_type])
            self.symbol_table.add_symbol(var_name, fake_type_tree)
            
            success_msg = f"Short declaration of '{var_name}' as '{expr_type}' OK"
            self.log_output(success_msg)
            self.log_event("SHORT_VAR_DECL_OK", success_msg)
        else:
            warning_msg = "WARNING: Multiple assignment for ':=' not implemented."
            self.log_output(warning_msg)
            self.log_event("MULTIPLE_SHORT_DECL_WARNING", warning_msg)

    def visit_BinaryExpr(self, node):
        """SDT Rule: In binary operation, check types and return result type."""
        self.log_output(f"Processing binary expression")
        op_node = node[1]
        operator = op_node[0] if isinstance(op_node, list) and len(op_node) > 0 else str(op_node)
        self.log_event("BINARY_EXPR_START", f"Operator: {operator}")
        
        left_type = self.visit(node[0])
        self.log_output(f"Left operand type: '{left_type}'")
        
        right_type = self.visit(node[2])
        self.log_output(f"Right operand type: '{right_type}'")
        
        if left_type != 'int' or right_type != 'int':
            error_msg = f"SDT Error: Operation '{operator}' only supports 'int' with 'int', not '{left_type}' with '{right_type}'"
            self.log_output(error_msg)
            self.log_event("TYPE_MISMATCH_ERROR", error_msg)
            raise SemanticError(error_msg)
        
        result_msg = f"Binary operation '{operator}' OK (int with int)"
        self.log_output(result_msg)
        self.log_event("BINARY_EXPR_OK", result_msg)
        
        return 'int'

    def visit_PackageClause(self, node):
        """SDT Rule: Handles the 'package' clause."""
        package_name = node[0][0] if node and len(node) > 0 and node[0] else "unknown"
        self.log_output(f"Processing package clause: {package_name}")
        self.log_event("PACKAGE_CLAUSE", f"Package: {package_name}")
        # No hacemos nada. No visitamos a los hijos (como Identifier("main"))
        pass

    def visit_Identifier(self, node):
        """SDT Rule: When using a variable, look it up and return its type."""
        var_name = node[0]
        self.log_output(f"Looking up identifier: '{var_name}'")
        self.log_event("IDENTIFIER_LOOKUP", f"Variable: {var_name}")
        
        try:
            var_type = self.symbol_table.lookup_symbol(var_name)
            self.log_output(f"Identifier '{var_name}' found with type '{var_type}'")
            self.log_event("IDENTIFIER_FOUND", f"'{var_name}' as {var_type}")
            return var_type
        except SemanticError as e:
            self.log_output(f"Warning: {str(e)}")
            self.log_event("IDENTIFIER_NOT_FOUND", f"'{var_name}' not declared")
            # Re-raise the exception to maintain original behavior
            raise

    def visit_IntLiteral(self, node):
        value = node[0] if node and len(node) > 0 else "0"
        self.log_debug(f"Integer literal: {value}")
        self.log_event("INT_LITERAL", f"Value: {value}")
        return 'int'

    def visit_StringLiteral(self, node):
        value = node[0] if node and len(node) > 0 else ""
        self.log_debug(f"String literal: '{value}'")
        self.log_event("STRING_LITERAL", f"Value: '{value}'")
        return 'string'

    def visit_FloatLiteral(self, node):
        value = node[0] if node and len(node) > 0 else "0.0"
        self.log_debug(f"Float literal: {value}")
        self.log_event("FLOAT_LITERAL", f"Value: {value}")
        return 'float64'

    def visit_BoolLiteral(self, node):
        value = node[0] if node and len(node) > 0 else "false"
        self.log_debug(f"Boolean literal: {value}")
        self.log_event("BOOL_LITERAL", f"Value: {value}")
        return 'bool'

    def visit_QualifiedIdent(self, node):
        """SDT Rule: Process qualified identifier (e.g., fmt.Println)"""
        self.log_output(f"Processing qualified identifier")
        self.log_event("QUALIFIED_IDENT_START", "Qualified identifier")
        
        if len(node) >= 2:
            package_node = node[0]
            ident_node = node[1]
            
            package_name = package_node[0] if isinstance(package_node, Tree) else str(package_node)
            ident_name = ident_node[0] if isinstance(ident_node, Tree) else str(ident_node)
            
            self.log_output(f"Qualified identifier: {package_name}.{ident_name}")
            self.log_event("QUALIFIED_IDENT", f"{package_name}.{ident_name}")
            
            # Para funciones como fmt.Println, no necesitamos declararlas como variables
            # Simplemente devolvemos un tipo apropiado
            if package_name == "fmt" and ident_name in ["Println", "Print", "Printf"]:
                self.log_output(f"Standard library function: {package_name}.{ident_name}")
                self.log_event("STD_FUNCTION", f"{package_name}.{ident_name}")
                return "void"  # O el tipo apropiado para funciones de impresión
        else:
            self.log_debug(f"Qualified identifier with unexpected structure")
        
        # En otros casos, intentamos procesar el identificador derecho
        if len(node) > 1:
            right_type = self.visit(node[1])
            return right_type
        
        return "unknown"

    # Métodos adicionales para tipos de nodos comunes
    def visit_SimpleType(self, node):
        type_name = node[0] if node and len(node) > 0 else "unknown"
        self.log_debug(f"Simple type: {type_name}")
        return type_name

    def visit_ExpressionList(self, node):
        self.log_debug(f"Processing expression list with {len(node)} expression(s)")
        results = []
        for i, expr in enumerate(node):
            self.log_debug(f"Processing expression {i+1} in list")
            result = self.visit(expr)
            results.append(result)
        return results

    def visit_StatementList(self, node):
        self.log_debug(f"Processing statement list with {len(node)} statement(s)")
        for i, stmt in enumerate(node):
            self.log_debug(f"Processing statement {i+1} in list")
            self.visit(stmt)

    def visit_IfStmt(self, node):
        """SDT Rule: Process if statement"""
        self.log_output(f"Processing if statement")
        self.log_event("IF_STMT_START", "If statement")
        
        condition = node[0]
        self.log_output(f"Evaluating if condition")
        cond_type = self.visit(condition)
        
        if cond_type != 'bool':
            warning_msg = f"Warning: If condition should be boolean, got '{cond_type}'"
            self.log_output(warning_msg)
            self.log_event("IF_CONDITION_WARNING", warning_msg)
        
        true_block = node[1]
        self.log_output(f"Processing if true block")
        self.visit(true_block)
        
        if len(node) > 2:  # Tiene else/else if
            false_block = node[2]
            self.log_output(f"Processing else block")
            self.visit(false_block)
        
        self.log_event("IF_STMT_END", "If statement completed")

    def visit_ForStmt(self, node):
        """SDT Rule: Process for statement"""
        self.log_output(f"Processing for statement")
        self.log_event("FOR_STMT_START", "For statement")
        
        # Visitar componentes del for
        self.generic_visit(node)
        
        self.log_event("FOR_STMT_END", "For statement completed")

    def visit_ReturnStmt(self, node):
        """SDT Rule: Process return statement"""
        self.log_output(f"Processing return statement")
        self.log_event("RETURN_STMT", "Return statement")
        
        if node:
            return_type = self.visit(node[0])
            self.log_output(f"Return statement with type: {return_type}")
            return return_type
        
        self.log_output(f"Return statement without value (void)")
        return "void"

    def visit_CallExpr(self, node):
        """SDT Rule: Process function call"""
        self.log_output(f"Processing function call")
        self.log_event("FUNCTION_CALL_START", "Function call")
        
        # Visitar el identificador de la función
        func_node = node[0]
        if isinstance(func_node, Tree):
            if func_node.label() == 'QualifiedIdent':
                func_name = f"{func_node[0][0]}.{func_node[1][0]}"
            else:
                func_name = func_node[0] if len(func_node) > 0 else "unknown"
        else:
            func_name = str(func_node)
        
        self.log_output(f"Calling function: {func_name}")
        
        # Visitar argumentos si existen
        if len(node) > 1:
            args_node = node[1]
            self.log_output(f"Processing function arguments")
            self.visit(args_node)
        
        self.log_event("FUNCTION_CALL_END", f"Function: {func_name}")
        
        # Para funciones conocidas, devolver tipos apropiados
        if func_name == "fmt.Println":
            return "void"
        
        # Para otras funciones, asumimos que devuelven int por ahora
        return "int"

    def visit_ArgumentList(self, node):
        self.log_debug(f"Processing argument list with {len(node)} argument(s)")
        arg_types = []
        for i, arg in enumerate(node):
            self.log_debug(f"Processing argument {i+1}")
            arg_type = self.visit(arg)
            arg_types.append(arg_type)
        
        self.log_debug(f"Argument types: {arg_types}")
        return arg_types

    def visit_IncDecStmt(self, node):
        """SDT Rule: Process increment/decrement statement"""
        var_node = node[0]
        op_node = node[1]
        
        var_name = var_node[0] if isinstance(var_node, Tree) else str(var_node)
        operator = op_node[0] if isinstance(op_node, list) else str(op_node)
        
        self.log_output(f"Processing {operator} operation on '{var_name}'")
        self.log_event("INC_DEC_STMT", f"{operator} on {var_name}")
        
        # Verificar que la variable existe
        var_type = self.symbol_table.lookup_symbol(var_name)
        
        if var_type != 'int':
            error_msg = f"SDT Error: {operator} operation only works on 'int', not '{var_type}'"
            self.log_output(error_msg)
            self.log_event("INC_DEC_TYPE_ERROR", error_msg)
            raise SemanticError(error_msg)
        
        self.log_output(f"{operator} operation on '{var_name}' OK")
        return var_type

    def visit_Operator(self, node):
        """SDT Rule: Process operator"""
        operator = node[0] if node and len(node) > 0 else "unknown"
        self.log_debug(f"Operator: {operator}")
        return operator