# modules/tac_nasm.py
import re
from pathlib import Path
import subprocess
import os

class TACToNASM64:
    def __init__(self):
        self.asm_code = []
        self.text_section = []
        self.data_section = []
        self.bss_section = []
        self.data_labels = set()
        self.string_data = {}
        
        # Para seguimiento de funciones
        self.current_function = None
        self.functions = {}  # name -> {'params': [], 'locals': {}, 'temp_count': 0}
        self.local_vars = {}  # var_name -> stack_offset
        self.param_vars = {}  # param_name -> register/stack_offset
        self.temp_count = 0
        self.label_count = 0
        
        # Variables globales
        self.global_vars = set()
        
        # Para alineación de pila
        self.stack_used = 0
        self.max_stack_used = 0
        
    def convert_tac_file(self, tac_file_path):
        """Convierte un archivo TAC a NASM 64-bit"""
        if not Path(tac_file_path).exists():
            print(f"Error: Archivo TAC no encontrado: {tac_file_path}")
            return None
            
        # Leer el archivo TAC
        with open(tac_file_path, 'r', encoding='utf-8') as f:
            tac_content = f.read()
        
        # Buscar la sección TAC
        if "THREE ADDRESS CODE (TAC):" in tac_content:
            # Extraer solo las líneas TAC
            lines = tac_content.split('\n')
            in_tac_section = False
            tac_instructions = []
            
            for line in lines:
                if "THREE ADDRESS CODE (TAC):" in line:
                    in_tac_section = True
                    continue
                if in_tac_section and "===" in line:  # Saltar líneas de separación
                    continue
                if in_tac_section and line.strip() and not line.startswith("="):
                    tac_instructions.append(line.strip())
        else:
            # Si no hay marcador, usar todo el contenido
            lines = tac_content.strip().split('\n')
            tac_instructions = [line.strip() for line in lines if line.strip()]
        
        return self.convert_tac_instructions(tac_instructions)
    
    def convert_tac_instructions(self, tac_instructions):
        """Convierte instrucciones TAC a NASM 64-bit"""
        self.asm_code = []
        self.text_section = []
        self.data_section = []
        self.bss_section = []
        self.functions = {}
        self.current_function = None
        self.local_vars = {}
        self.param_vars = {}
        self.temp_count = 0
        self.label_count = 0
        self.global_vars = set()
        self.stack_used = 0
        self.max_stack_used = 0
        
        # Preprocesar TAC
        tac_instructions = self.preprocess_tac(tac_instructions)
        
        # Primera pasada: identificar funciones y variables
        self.analyze_functions(tac_instructions)
        
        # Segunda pasada: generar código
        self.generate_code(tac_instructions)
        
        # Construir el código NASM final
        return self.build_nasm_code()
    
    def analyze_functions(self, tac_instructions):
        """Primera pasada: identificar funciones y sus variables"""
        current_func = None
        in_function = False
        
        for line in tac_instructions:
            if line.endswith(':'):
                label = line.rstrip(':')
                if label.startswith("FUNC "):
                    func_name = label[5:]
                    self.functions[func_name] = {
                        'params': [],
                        'locals': set(),
                        'temps': set(),
                        'start_line': tac_instructions.index(line)
                    }
                    current_func = func_name
                    in_function = True
                elif label.startswith("END_FUNC"):
                    in_function = False
                    current_func = None
            elif in_function and current_func:
                # Analizar variables locales y temporales
                if " = " in line:
                    dest_part = line.split(" = ", 1)[0].strip()
                    if dest_part.startswith('t'):
                        self.functions[current_func]['temps'].add(dest_part)
                    elif dest_part not in ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 
                                         'rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi']:
                        # Verificar si no es un parámetro
                        if not (dest_part in ['n', 'i', 'param1', 'param2', 'param3', 'param4']):
                            self.functions[current_func]['locals'].add(dest_part)
    
    def generate_code(self, tac_instructions):
        """Segunda pasada: generar código NASM"""
        for line in tac_instructions:
            self.process_tac_line(line)
    
    def build_nasm_code(self):
        """Construir el código NASM final con secciones correctas"""
        nasm_code = []
        
        # Directivas globales
        nasm_code.append("default rel")
        nasm_code.append("")
        
        # Sección de datos (constantes) - ¡IMPORTANTE! Definir fmt_int aquí
        nasm_code.append("section .data")
        nasm_code.append('    fmt_int db "%d", 10, 0')
        nasm_code.append('    fmt_float db "%.2f", 10, 0')
        nasm_code.append('    fmt_string db "%s", 10, 0')
        nasm_code.append("")
        
        # Añadir datos personalizados si los hay
        if self.string_data:
            nasm_code.extend(self.string_data)
            nasm_code.append("")
        if self.data_section:
            nasm_code.extend(self.data_section)
            nasm_code.append("")
        
        # Sección BSS (variables globales sin inicializar)
        if self.bss_section:
            nasm_code.append("section .bss")
            nasm_code.extend(self.bss_section)
            nasm_code.append("")
        
        # Sección de texto (código)
        nasm_code.append("section .text")
        nasm_code.append("global main")
        nasm_code.append("extern printf, exit")
        nasm_code.append("")
        
        # Añadir código de texto
        nasm_code.extend(self.text_section)
        
        return "\n".join(nasm_code)
    
    def add_header(self):
        """Añade cabecera para la función main"""
        self.text_section.append("main:")
        self.text_section.append("    push rbp")
        self.text_section.append("    mov rbp, rsp")
        # Reservar espacio para shadow space + variables locales si las hay
        self.text_section.append("    sub rsp, 32")
    
    def preprocess_tac(self, tac_instructions):
        """Preprocesa instrucciones TAC para hacerlas más consistentes"""
        processed = []
        string_data = []
        
        for line in tac_instructions:
            # Extraer declaraciones de datos de cadena
            if line.startswith("DATA "):
                parts = line[5:].split(" = ", 1)
                if len(parts) == 2:
                    label = parts[0].strip()
                    value = parts[1].strip()
                    # store raw value and data label
                    self.data_labels.add(label)
                    self.string_data[label] = value
                    # convert to a proper data directive
                    string_data.append(f"    {label}: db {value}, 0")
                continue
            
            # Convertir operadores TAC a operadores normales
            line = line.replace(" ADD ", " + ")
            line = line.replace(" SUB ", " - ")
            line = line.replace(" MUL ", " * ")
            line = line.replace(" DIV ", " / ")
            line = line.replace(" LE ", " <= ")
            line = line.replace(" LT ", " < ")
            line = line.replace(" GE ", " >= ")
            line = line.replace(" GT ", " > ")
            line = line.replace(" EQ ", " == ")
            line = line.replace(" NE ", " != ")
            
            # Quitar espacios extra
            line = ' '.join(line.split())
            processed.append(line)
        
        # Guardar datos de cadena
        # string_data are lines like 'label: db "..." , 0'
        self.string_data = string_data
        return processed
    
    # En tac_nasm.py - Añadir esta mejora en process_tac_line
    def process_tac_line(self, line):
        """Procesa una línea TAC individual"""
        line = line.strip()
        if not line:
            return
        
        # DEBUG
        # print(f"[TAC→NASM] Procesando: '{line}'")
        
        # 1. Manejar etiquetas y funciones
        if line.endswith(':'):
            self.process_label(line)
            return
        
        # 2. Manejar llamadas a funciones con asignación
        # Detectar patrones como: tX = CALL funcion arg1 arg2 ...
        call_pattern = r'^(t\d+)\s*=\s*CALL\s+(\w+(?:\.\w+)?)(?:\s+(.+))?$'
        match = re.match(call_pattern, line)
        if match:
            dest = match.group(1)
            func_name = match.group(2)
            args_str = match.group(3) or ""
            args = args_str.split() if args_str else []
            
            # Procesar la llamada a función
            self.text_section.append(f"    ; {line}")
            if func_name == "fmt.Println":
                self.process_println_call(args)
            else:
                self.process_function_call(func_name, args, True, dest)
            return
        
        # 3. Manejar llamadas a funciones sin asignación
        # Detectar patrones como: CALL funcion arg1 arg2 ...
        call_no_dest_pattern = r'^CALL\s+(\w+(?:\.\w+)?)(?:\s+(.+))?$'
        match = re.match(call_no_dest_pattern, line)
        if match:
            func_name = match.group(1)
            args_str = match.group(2) or ""
            args = args_str.split() if args_str else []
            
            # Procesar la llamada a función
            self.text_section.append(f"    ; {line}")
            if func_name == "fmt.Println":
                self.process_println_call(args)
            else:
                self.process_function_call(func_name, args, False, None)
            return
        
        # 4. Manejar instrucciones de control
        control_instructions = {
            'GOTO ': self.process_goto,
            'IF_TRUE ': self.process_if_true,
            'IF_FALSE ': self.process_if_false,
            'RETURN': self.process_return,
            'END_FUNC': self.process_end_func,
        }
        
        for prefix, handler in control_instructions.items():
            if line.startswith(prefix):
                handler(line)
                return
        
        # 5. Manejar asignaciones
        if " = " in line:
            self.process_assignment(line)
            return
        
        # 6. Instrucción no reconocida
        self.text_section.append(f"    ; {line} (no procesada)")

    
    def process_label(self, line):
        """Procesa una etiqueta o función"""
        label = line.rstrip(':')
        
        if label.startswith("FUNC "):
            func_name = label[5:]
            self.enter_function(func_name)
            self.text_section.append(f"{func_name}:")
            
            # Prolog de función
            self.text_section.append("    push rbp")
            self.text_section.append("    mov rbp, rsp")
            
            # Reservar espacio para variables locales y alineación
            local_space = self.calculate_local_space(func_name)
            if local_space > 0:
                self.text_section.append(f"    sub rsp, {local_space}")
                self.stack_used = local_space
                if local_space > self.max_stack_used:
                    self.max_stack_used = local_space
            
            # Shadow space para llamadas a funciones
            self.text_section.append("    sub rsp, 32")
            
        elif label.startswith("LABEL "):
            label_name = label[6:]
            self.text_section.append(f"{label_name}:")
        else:
            self.text_section.append(f"{label}:")
    
    def enter_function(self, func_name):
        """Entrar en una nueva función"""
        self.current_function = func_name
        self.local_vars = {}
        self.param_vars = {}
        self.temp_count = 0
        
        # Asignar offsets para parámetros (convención Windows x64)
        # Primer parámetro: RCX -> [rbp+16]
        # Segundo parámetro: RDX -> [rbp+24]
        # Tercer parámetro: R8 -> [rbp+32]
        # Cuarto parámetro: R9 -> [rbp+40]
        
        # Guardar parámetros en la pila local
        param_offsets = [16, 24, 32, 40]
        
        if func_name in self.functions:
            # Simular parámetros básicos
            self.param_vars['n'] = '[rbp+16]'  # Primer parámetro
            # Podemos añadir más parámetros según sea necesario
    
    def calculate_local_space(self, func_name):
        """Calcula el espacio necesario para variables locales"""
        if func_name not in self.functions:
            return 0
        
        local_count = len(self.functions[func_name]['locals'])
        temp_count = len(self.functions[func_name]['temps'])
        
        # Cada variable necesita 4 bytes (dword) o 8 bytes (qword)
        # Para simplicidad, usamos 8 bytes cada una y alineamos a 16 bytes
        total_vars = local_count + temp_count
        space_needed = total_vars * 8
        
        # Alinear a múltiplo de 16
        if space_needed % 16 != 0:
            space_needed = ((space_needed // 16) + 1) * 16
        
        return space_needed
    
    def get_var_stack_offset(self, var_name):
        """Obtiene el offset de pila para una variable local"""
        if var_name in self.param_vars:
            return self.param_vars[var_name]
        
        if var_name not in self.local_vars:
            # Asignar nuevo offset
            offset = -8 - (len(self.local_vars) * 8)
            self.local_vars[var_name] = f"[rbp{offset:+d}]"
        
        return self.local_vars[var_name]
    
    def process_goto(self, line):
        """Procesa GOTO"""
        label = line[5:]  # Quitar "GOTO "
        self.text_section.append(f"    jmp {label}")
    
    def process_if_true(self, line):
        """Procesa IF_TRUE cond GOTO label"""
        parts = line.split()
        if len(parts) >= 4 and parts[2] == "GOTO":
            cond_var = parts[1]
            label = parts[3]
            
            # Obtener ubicación de la variable condicional
            if cond_var in self.local_vars:
                cond_loc = self.local_vars[cond_var]
            elif cond_var in self.param_vars:
                cond_loc = self.param_vars[cond_var]
            else:
                cond_loc = f"[{cond_var}]"  # Variable global
            
            self.text_section.append(f"    cmp dword {cond_loc}, 0")
            self.text_section.append(f"    jne {label}")
    
    def process_if_false(self, line):
        """Procesa IF_FALSE cond GOTO label"""
        parts = line.split()
        if len(parts) >= 4 and parts[2] == "GOTO":
            cond_var = parts[1]
            label = parts[3]
            
            # Obtener ubicación de la variable condicional
            if cond_var in self.local_vars:
                cond_loc = self.local_vars[cond_var]
            elif cond_var in self.param_vars:
                cond_loc = self.param_vars[cond_var]
            else:
                cond_loc = f"[{cond_var}]"  # Variable global
            
            self.text_section.append(f"    cmp dword {cond_loc}, 0")
            self.text_section.append(f"    je {label}")
    
    def process_return(self, line):
        """Procesa RETURN"""
        self.text_section.append(f"    ; {line}")
        
        if len(line) > 6:  # Tiene valor
            ret_val = line[7:].strip()
            
            # Cargar valor de retorno en EAX
            if ret_val.isdigit() or (ret_val[0] == '-' and ret_val[1:].isdigit()):
                self.text_section.append(f"    mov eax, {ret_val}")
            else:
                # Obtener ubicación de la variable
                if ret_val in self.local_vars:
                    ret_loc = self.local_vars[ret_val]
                elif ret_val in self.param_vars:
                    ret_loc = self.param_vars[ret_val]
                else:
                    ret_loc = f"[{ret_val}]"  # Variable global
                
                self.text_section.append(f"    mov eax, {ret_loc}")
        else:
            self.text_section.append("    xor eax, eax")
        
        # Epilog de función
        self.text_section.append("    mov rsp, rbp")
        self.text_section.append("    pop rbp")
        self.text_section.append("    ret")
    
    def process_end_func(self, line):
        """Procesa END_FUNC"""
        self.text_section.append("    ; END_FUNC")
        
        # Epilog de función
        self.text_section.append("    mov rsp, rbp")
        self.text_section.append("    pop rbp")
        self.text_section.append("    ret")
        
        # Salir de la función actual
        self.current_function = None
    
    def process_call(self, line):
        """Procesa CALL"""
        parts = line.split()
        if len(parts) < 2:
            return
        
        func_name = parts[1]
        args = parts[2:] if len(parts) > 2 else []
        
        # Verificar si hay destino: tX = CALL ...
        has_dest = '=' in line
        dest = None
        if has_dest:
            dest = line.split('=')[0].strip()
        
        self.text_section.append(f"    ; {line}")
        
        if func_name == "fmt.Println":
            self.process_println_call(args)
        else:
            self.process_function_call(func_name, args, has_dest, dest)
    
    def process_println_call(self, args):
        """Procesa CALL fmt.Println"""
        if not args:
            return
        
        arg = args[0]
        
        # DEBUG
        self.text_section.append(f"    ; PRINTLN: {arg}")
        
        # Shadow space (32 bytes para convención Windows x64)
        self.text_section.append("    sub rsp, 32")
        
        # Preparar argumento para printf
        # If argument is a known data label (string), pass string pointer and use fmt_string
        if arg in self.data_labels:
            # load format in RCX, string pointer in RDX (Windows x64, printf(format, arg))
            self.text_section.append(f"    lea rcx, [fmt_string]")
            # use RIP-relative LEA for global label
            self.text_section.append(f"    lea rdx, [{arg}]")
            self.text_section.append("    call printf")
        elif arg.isdigit() or (arg[0] == '-' and arg[1:].isdigit()):
            # integer literal
            self.text_section.append(f"    mov edx, {arg}")
            self.text_section.append("    lea rcx, [fmt_int]")
            self.text_section.append("    call printf")
        else:
            # treat as variable: get location
            var_loc = self.get_var_location(arg)
            # if location is memory, move into eax then to edx
            if '[' in var_loc:
                self.text_section.append(f"    mov eax, {var_loc}")
                self.text_section.append(f"    mov edx, eax")
            else:
                self.text_section.append(f"    mov edx, {var_loc}")
            self.text_section.append("    lea rcx, [fmt_int]")
            self.text_section.append("    call printf")
        
        # Restaurar pila
        self.text_section.append("    add rsp, 32")
        
        # DEBUG
        self.text_section.append("    ; Fin de println")
    
    def get_var_location(self, var_name):
        """Obtiene la ubicación de una variable"""
        if self.current_function:
            if var_name in self.local_vars:
                return self.local_vars[var_name]
            elif var_name in self.param_vars:
                return self.param_vars[var_name]
        
        # Variable global
        if var_name not in self.global_vars:
            self.global_vars.add(var_name)
            self.bss_section.append(f"    {var_name} resd 1")
        
        return f"[{var_name}]"
    
    def process_function_call(self, func_name, args, has_dest, dest):
        """Procesa llamada a función de usuario"""
        self.text_section.append(f"    ; CALL {func_name}")
        
        # Guardar registros no preservados
        self.text_section.append("    push rcx")
        self.text_section.append("    push rdx")
        self.text_section.append("    push r8")
        self.text_section.append("    push r9")
        
        # Pasar argumentos según convención Windows x64
        for i, arg in enumerate(args[:4]):  # Solo primeros 4 por registros
            if i == 0:
                reg = "rcx"
            elif i == 1:
                reg = "rdx"
            elif i == 2:
                reg = "r8"
            elif i == 3:
                reg = "r9"
            
            if arg.isdigit() or (arg[0] == '-' and arg[1:].isdigit()):
                self.text_section.append(f"    mov {reg}, {arg}")
            else:
                var_loc = self.get_var_location(arg)
                self.text_section.append(f"    mov {reg}, {var_loc}")
        
        # Shadow space
        self.text_section.append("    sub rsp, 32")
        
        # Llamar a la función
        self.text_section.append(f"    call {func_name}")
        
        # Restaurar pila
        self.text_section.append("    add rsp, 32")
        
        # Restaurar registros
        self.text_section.append("    pop r9")
        self.text_section.append("    pop r8")
        self.text_section.append("    pop rdx")
        self.text_section.append("    pop rcx")
        
        # Guardar resultado si hay destino
        if has_dest and dest:
            dest_loc = self.get_var_location(dest)
            self.text_section.append(f"    mov {dest_loc}, eax")
    
    def process_assignment(self, line):
        """Procesa asignación x = y o x = y op z"""
        dest_part, expr = line.split(" = ", 1)
        dest = dest_part.strip()
        
        self.text_section.append(f"    ; {line}")
        
        # Obtener ubicación de destino
        dest_loc = self.get_var_location(dest)
        
        # Verificar si es operación binaria
        operators = [' + ', ' - ', ' * ', ' <= ', ' < ', ' >= ', ' > ', ' == ', ' != ']
        is_binary_op = any(op in expr for op in operators)
        
        if not is_binary_op:
            # Asignación simple: x = y
            self.process_simple_assignment(dest_loc, expr.strip())
        else:
            # Operación binaria: x = y op z
            self.process_binary_operation(dest_loc, expr)
    
    def process_simple_assignment(self, dest_loc, src):
        """Procesa asignación simple x = y"""
        if src.isdigit() or (src[0] == '-' and src[1:].isdigit()):
            self.text_section.append(f"    mov dword {dest_loc}, {src}")
        else:
            # Obtener ubicación de la fuente
            src_loc = self.get_var_location(src)
            self.text_section.append(f"    mov eax, {src_loc}")
            self.text_section.append(f"    mov {dest_loc}, eax")
    
    def process_binary_operation(self, dest_loc, expr):
        """Procesa operación binaria x = y op z"""
        # Encontrar operador
        for op in [' <= ', ' < ', ' >= ', ' > ', ' == ', ' != ', ' + ', ' - ', ' * ', ' / ']:
            if op in expr:
                left, right = expr.split(op, 1)
                left = left.strip()
                right = right.strip()
                operator = op.strip()
                
                # Cargar izquierda
                if left.isdigit() or (left[0] == '-' and left[1:].isdigit()):
                    self.text_section.append(f"    mov eax, {left}")
                else:
                    left_loc = self.get_var_location(left)
                    self.text_section.append(f"    mov eax, {left_loc}")
                
                # Aplicar operación
                if operator in ['+', '-', '*']:
                    self.process_arithmetic_operation(operator, right)
                elif operator in ['<=', '<', '>=', '>', '==', '!=']:
                    self.process_comparison_operation(operator, right)
                elif operator == '/':
                    self.process_division_operation(right)
                
                # Guardar resultado
                self.text_section.append(f"    mov {dest_loc}, eax")
                break
    
    def process_arithmetic_operation(self, operator, right):
        """Procesa operación aritmética"""
        if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
            if operator == '+':
                self.text_section.append(f"    add eax, {right}")
            elif operator == '-':
                self.text_section.append(f"    sub eax, {right}")
            elif operator == '*':
                self.text_section.append(f"    imul eax, {right}")
        else:
            right_loc = self.get_var_location(right)
            if operator == '+':
                self.text_section.append(f"    add eax, {right_loc}")
            elif operator == '-':
                self.text_section.append(f"    sub eax, {right_loc}")
            elif operator == '*':
                self.text_section.append(f"    imul eax, {right_loc}")
    
    def process_division_operation(self, right):
        """Procesa operación de división (más compleja)"""
        # Para división, necesitamos preparar EDX:EAX
        self.text_section.append("    cdq")  # Extiende EAX a EDX:EAX
        
        if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
            self.text_section.append(f"    mov ecx, {right}")
            self.text_section.append("    idiv ecx")
        else:
            right_loc = self.get_var_location(right)
            self.text_section.append(f"    mov ecx, {right_loc}")
            self.text_section.append("    idiv ecx")
    
    def process_comparison_operation(self, operator, right):
        """Procesa operación de comparación"""
        cmp_label_true = f"cmp_true_{self.label_count}"
        cmp_label_end = f"cmp_end_{self.label_count}"
        self.label_count += 1
        
        # Comparar
        if right.isdigit() or (right[0] == '-' and right[1:].isdigit()):
            self.text_section.append(f"    cmp eax, {right}")
        else:
            right_loc = self.get_var_location(right)
            self.text_section.append(f"    cmp eax, {right_loc}")
        
        # Salto condicional según operador
        jump_instructions = {
            '<=': 'jle',
            '<': 'jl',
            '>=': 'jge',
            '>': 'jg',
            '==': 'je',
            '!=': 'jne'
        }
        
        if operator in jump_instructions:
            self.text_section.append(f"    {jump_instructions[operator]} {cmp_label_true}")
        
        self.text_section.append(f"    mov eax, 0")
        self.text_section.append(f"    jmp {cmp_label_end}")
        self.text_section.append(f"{cmp_label_true}:")
        self.text_section.append(f"    mov eax, 1")
        self.text_section.append(f"{cmp_label_end}:")


def write_nasm64_file(tac_file_path, output_dir=None):
    """Función principal para convertir TAC a NASM 64-bit y escribir archivo .asm"""
    try:
        converter = TACToNASM64()
        
        # Convertir TAC a NASM
        nasm_code = converter.convert_tac_file(tac_file_path)
        
        if not nasm_code:
            print("Error: Couldn't generate assembly code")
            return None
        
        # Determinar ruta de salida
        if output_dir is None:
            output_dir = Path(tac_file_path).parent
        
        output_name = Path(tac_file_path).stem.replace("_tac", "")
        output_path = output_dir / f"{output_name}.asm"
        
        # Añadir formatos de printf si no están
        if "fmt_int" not in nasm_code:
            nasm_code = nasm_code.replace("section .data", "section .data\n    fmt_int db \"%d\", 10, 0\n    fmt_float db \"%.2f\", 10, 0")
        
        # Escribir archivo NASM
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(nasm_code)
        
        print(f"NASM file generated")
        
        try:
            obj_path = output_dir / f"{output_name}.obj"
            exe_path = output_dir / f"{output_name}.exe"
            
            print(f"\nAssembling with NASM...")
            
            # Ensamblar con NASM
            result = subprocess.run(
                ["nasm", "-f", "win64", str(output_path), "-o", str(obj_path)],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error in NASM assembling:")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                return output_path
            
            print(f"Successful Assembling:")
            
            print(f"\nLinking with GCC...")
            
            # Enlazar con GCC
            result = subprocess.run(
                ["gcc", str(obj_path), "-o", str(exe_path)],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Error linking GCC:")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                return output_path
            
            print(f"Successful Linking:")
            
            # Verificar que el ejecutable se creó
            if exe_path.exists():                
                # Intentar ejecutar
                print(f"\n--- EXECUTING {exe_path.name} ---")
                result = subprocess.run(
                    [str(exe_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                print(f"Exit Code: {result.returncode}")
                if result.stdout:
                    print(f"Output: {result.stdout.strip()}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
            else:
                print(f"The executable was not created.")
            
            return exe_path
            
        except subprocess.TimeoutExpired:
            print("Timeout: NASM o GCC took too long to respond.")
            return output_path
        except FileNotFoundError as e:
            print(f"Command not founf: {e}")
            print("  Verify that NASM and GCC are installed and in your system PATH.")
            return output_path
        except Exception as e:
            print(f"Unexpected error: {e}")
            return output_path
            
    except Exception as e:
        print(f"Error in write_nasm64_file: {e}")
        import traceback
        traceback.print_exc()
        return None