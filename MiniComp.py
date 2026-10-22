# -*- coding: utf-8 -*-
"""
MiniComp - Generador de código intermedio (Unidad 2, Lenguajes y Autómatas II)

Soporta:
  * Declaraciones:  entero a = 8;   decimal p = 2.5;   entero r;
  * Asignaciones:   r = a + b * 2;
  * Condicional:    si (r > 10) { ... }   (comparadores <, >, <=, >=, ==, !=)
  * Llamadas:       imprimir(r);  cuadrado(a);  maximo(a, b);
  * Operadores:     + - * /  y paréntesis

Genera: tabla de símbolos, notaciones infija/prefija/postfija, cuádruplos y triplos.
Ejecutar:  python minicomp.py
"""
import re
from collections import namedtuple

# ---------------------------------------------------------------- Configuración
TIPOS = {"entero", "decimal"}
PALABRAS_RESERVADAS = TIPOS | {"si"}
FUNCIONES = {"imprimir": 1, "cuadrado": 1, "maximo": 2}  # nombre -> nº de parámetros
PRECEDENCIA = {"+": 1, "-": 1, "*": 2, "/": 2}

Token = namedtuple("Token", "tipo valor linea")


class ErrorCompilador(Exception):
    def __init__(self, mensaje, linea):
        super().__init__(mensaje)
        self.mensaje, self.linea = mensaje, linea


# ---------------------------------------------------------------- Analizador léxico
PATRON = re.compile(r"""
    (?P<ESP>[ \t\r]+) | (?P<NL>\n) |
    (?P<NUM>\d+\.\d+|\d+) |
    (?P<ID>[^\W\d]\w*) |
    (?P<CMP>==|!=|<=|>=|<|>) |
    (?P<OP>[+\-*/]) | (?P<ASIG>=) |
    (?P<LP>\() | (?P<RP>\)) | (?P<LL>\{) | (?P<RL>\}) |
    (?P<PYC>;) | (?P<COMA>,) | (?P<MAL>.)
""", re.X)


def tokenizar(texto):
    tokens, linea = [], 1
    for m in PATRON.finditer(texto):
        tipo, valor = m.lastgroup, m.group()
        if tipo == "NL":
            linea += 1
        elif tipo == "ESP":
            continue
        elif tipo == "MAL":
            raise ErrorCompilador(f"símbolo no admitido '{valor}'", linea)
        else:
            if tipo == "ID" and valor in PALABRAS_RESERVADAS:
                tipo = "KW"
            tokens.append(Token(tipo, valor, linea))
    tokens.append(Token("EOF", "", linea))
    return tokens


def verificar_balance(tokens):
    """Detecta paréntesis y llaves desbalanceados."""
    pila = []
    pares = {")": "(", "}": "{"}
    for t in tokens:
        if t.valor in "({" and t.tipo in ("LP", "LL"):
            pila.append(t)
        elif t.tipo in ("RP", "RL"):
            if not pila or pila[-1].valor != pares[t.valor]:
                raise ErrorCompilador(f"'{t.valor}' sin su pareja de apertura", t.linea)
            pila.pop()
    if pila:
        raise ErrorCompilador(f"'{pila[-1].valor}' sin cerrar", pila[-1].linea)


# ---------------------------------------------------------------- Notaciones
# Un nodo del árbol es: ("num", v) | ("id", v) | ("bin", op, izq, der)
def prefija(n):
    if n[0] != "bin":
        return [n[1]]
    return [n[1]] + prefija(n[2]) + prefija(n[3])


def postfija(n):
    if n[0] != "bin":
        return [n[1]]
    return postfija(n[2]) + postfija(n[3]) + [n[1]]


def unir_infija(tokens):
    s = " ".join(t.valor for t in tokens)
    return s.replace("( ", "(").replace(" )", ")")


# ---------------------------------------------------------------- Compilador
class MiniComp:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0
        self.simbolos = {}        # nombre -> (tipo, valor inicial)
        self.constantes = []      # literales numéricos encontrados
        self.cuadruplos = []      # (op, a1, a2, resultado)
        self.triplos = []         # (op, a1, a2)
        self.notaciones = []      # (infija, prefija, postfija)
        self.ntemp = 0
        self.netiq = 0

    # ---- utilidades del parser
    def actual(self):
        return self.t[self.i]

    def avanzar(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def esperar(self, tipo, mensaje):
        if self.actual().tipo != tipo:
            raise ErrorCompilador(mensaje, self.actual().linea)
        return self.avanzar()

    # ---- programa y sentencias
    def programa(self):
        verificar_balance(self.t)
        while self.actual().tipo != "EOF":
            self.sentencia()

    def sentencia(self):
        tok = self.actual()
        if tok.tipo == "KW" and tok.valor in TIPOS:
            self.declaracion()
        elif tok.tipo == "KW" and tok.valor == "si":
            self.condicional()
        elif tok.tipo == "ID" and self.t[self.i + 1].tipo == "LP":
            self.llamada()
        elif tok.tipo == "ID":
            self.asignacion()
        else:
            raise ErrorCompilador(f"instrucción no válida cerca de '{tok.valor}'", tok.linea)

    def declaracion(self):
        tipo = self.avanzar().valor
        nombre = self.esperar("ID", "se esperaba un identificador después del tipo")
        if nombre.valor in self.simbolos:
            raise ErrorCompilador(f"'{nombre.valor}' ya fue declarado", nombre.linea)
        valor = "-"
        if self.actual().tipo == "ASIG":
            self.avanzar()
            if self.actual().tipo == "PYC":
                raise ErrorCompilador("asignación sin expresión", self.actual().linea)
            nodo, texto = self.expresion()
            valor = nodo[1] if nodo[0] == "num" else texto
            self.registrar(nodo, texto)
            self.simbolos[nombre.valor] = (tipo, valor)
            self.generar_asignacion(nodo, nombre.valor)
        else:
            self.simbolos[nombre.valor] = (tipo, valor)
        self.esperar("PYC", "falta ';' al final de la declaración")

    def asignacion(self):
        nombre = self.avanzar()
        if nombre.valor not in self.simbolos:
            raise ErrorCompilador(f"identificador '{nombre.valor}' no declarado", nombre.linea)
        self.esperar("ASIG", "se esperaba '=' en la asignación")
        if self.actual().tipo == "PYC":
            raise ErrorCompilador("asignación sin expresión", self.actual().linea)
        nodo, texto = self.expresion()
        self.registrar(nodo, texto)
        self.esperar("PYC", "falta ';' al final de la asignación")
        self.generar_asignacion(nodo, nombre.valor)

    def condicional(self):
        self.avanzar()  # 'si'
        self.esperar("LP", "se esperaba '(' después de 'si'")
        izq, ti = self.expresion()
        if self.actual().tipo != "CMP":
            raise ErrorCompilador("se esperaba un comparador (<, >, ==, !=)", self.actual().linea)
        cmp_ = self.avanzar().valor
        der, td = self.expresion()
        self.esperar("RP", "falta ')' en la condición")
        self.esperar("LL", "se esperaba '{' después de la condición")
        self.registrar(izq, ti)
        self.registrar(der, td)
        # Código de la condición
        a_c, b_c = self.gen_cuad(izq), self.gen_cuad(der)
        etiqueta = self.nueva_etiqueta()
        t = self.nuevo_temp()
        self.cuadruplos.append((cmp_, a_c, b_c, t))
        self.cuadruplos.append(("IF_FALSE", t, "-", etiqueta))
        a_t, b_t = self.gen_trip(izq), self.gen_trip(der)
        ref = self.emitir_trip(cmp_, a_t, b_t)
        self.emitir_trip("IF_FALSE", ref, etiqueta)
        # Cuerpo
        while self.actual().tipo not in ("RL", "EOF"):
            self.sentencia()
        self.esperar("RL", "falta '}' al cerrar el bloque 'si'")
        self.cuadruplos.append(("LABEL", "-", "-", etiqueta))
        self.emitir_trip("LABEL", etiqueta)

    def llamada(self):
        nombre = self.avanzar()
        if nombre.valor not in FUNCIONES:
            raise ErrorCompilador(f"función '{nombre.valor}' no definida", nombre.linea)
        self.esperar("LP", "se esperaba '('")
        args = []
        if self.actual().tipo != "RP":
            while True:
                nodo, texto = self.expresion()
                self.registrar(nodo, texto)
                args.append(nodo)
                if self.actual().tipo == "COMA":
                    self.avanzar()
                else:
                    break
        self.esperar("RP", "falta ')' en la llamada")
        self.esperar("PYC", "falta ';' al final de la llamada")
        if len(args) != FUNCIONES[nombre.valor]:
            raise ErrorCompilador(
                f"'{nombre.valor}' espera {FUNCIONES[nombre.valor]} parámetro(s) y recibió {len(args)}",
                nombre.linea)
        for a in args:
            self.cuadruplos.append(("PARAM", self.gen_cuad(a), "-", "-"))
            self.emitir_trip("PARAM", self.gen_trip(a))
        self.cuadruplos.append(("CALL", nombre.valor, len(args), "-"))
        self.emitir_trip("CALL", nombre.valor, len(args))

    # ---- expresiones (descenso recursivo; respeta precedencia y paréntesis)
    def expresion(self):
        inicio = self.i
        nodo = self.suma()
        return nodo, unir_infija(self.t[inicio:self.i])

    def suma(self):
        nodo = self.termino()
        while self.actual().tipo == "OP" and self.actual().valor in "+-":
            op = self.avanzar().valor
            nodo = ("bin", op, nodo, self.termino())
        return nodo

    def termino(self):
        nodo = self.factor()
        while self.actual().tipo == "OP" and self.actual().valor in "*/":
            op = self.avanzar().valor
            nodo = ("bin", op, nodo, self.factor())
        return nodo

    def factor(self):
        tok = self.actual()
        if tok.tipo == "NUM":
            self.avanzar()
            if tok.valor not in self.constantes:
                self.constantes.append(tok.valor)
            return ("num", tok.valor)
        if tok.tipo == "ID":
            self.avanzar()
            if tok.valor not in self.simbolos:
                raise ErrorCompilador(f"identificador '{tok.valor}' no declarado", tok.linea)
            return ("id", tok.valor)
        if tok.tipo == "LP":
            self.avanzar()
            nodo = self.suma()
            self.esperar("RP", "falta ')' para cerrar la expresión")
            return nodo
        raise ErrorCompilador("expresión incompleta: se esperaba número, identificador o '('",
                              tok.linea)

    # ---- generación de código intermedio
    def nuevo_temp(self):
        self.ntemp += 1
        return f"t{self.ntemp}"

    def nueva_etiqueta(self):
        self.netiq += 1
        return f"L{self.netiq}"

    def emitir_trip(self, op, a1, a2=None):
        self.triplos.append((op, a1) if a2 is None else (op, a1, a2))
        return f"({len(self.triplos)})"

    def gen_cuad(self, n):
        """Devuelve el operando; si es operación, crea el cuádruplo con un temporal."""
        if n[0] != "bin":
            return n[1]
        a, b = self.gen_cuad(n[2]), self.gen_cuad(n[3])
        t = self.nuevo_temp()
        self.cuadruplos.append((n[1], a, b, t))
        return t

    def gen_trip(self, n):
        """Devuelve el operando; si es operación, crea el triplo y regresa su referencia (n)."""
        if n[0] != "bin":
            return n[1]
        a, b = self.gen_trip(n[2]), self.gen_trip(n[3])
        return self.emitir_trip(n[1], a, b)

    def generar_asignacion(self, nodo, destino):
        self.cuadruplos.append(("=", self.gen_cuad(nodo), "-", destino))
        self.emitir_trip("=", self.gen_trip(nodo), destino)

    def registrar(self, nodo, texto):
        """Guarda las 3 notaciones solo para expresiones con operadores."""
        if nodo[0] == "bin":
            self.notaciones.append((texto, " ".join(prefija(nodo)), " ".join(postfija(nodo))))


# ---------------------------------------------------------------- Presentación
def titulo(texto):
    print("\n" + "=" * 52 + f"\n {texto}\n" + "=" * 52)


def procesar(texto):
    try:
        comp = MiniComp(tokenizar(texto))
        comp.programa()
    except ErrorCompilador as e:
        print(f"\n[ERROR] Línea {e.linea}: {e.mensaje}")
        return

    titulo("1. TABLA DE SÍMBOLOS")
    print(f"{'Identificador':<15}{'Tipo':<10}{'Valor inicial'}")
    for nombre, (tipo, valor) in comp.simbolos.items():
        print(f"{nombre:<15}{tipo:<10}{valor}")
    print("Constantes:", ", ".join(comp.constantes) or "(ninguna)")

    titulo("2. NOTACIONES")
    for infija, pre, post in comp.notaciones:
        print(f"Infija : {infija}\nPrefija: {pre}\nPostfija: {post}\n")
    if not comp.notaciones:
        print("(no hay expresiones con operadores)")

    titulo("3. CUÁDRUPLOS")
    for n, c in enumerate(comp.cuadruplos, 1):
        print(f"({n}) ({', '.join(str(x) for x in c)})")

    titulo("4. TRIPLOS")
    for n, t in enumerate(comp.triplos, 1):
        print(f"({n}) ({', '.join(str(x) for x in t)})")


EJEMPLO = """entero a = 8;
entero b = 3;
entero resultado;
resultado = a + b * 2;
si (resultado > 10) {
    resultado = resultado - 1;
}
imprimir(resultado);
"""

PRUEBAS = """decimal precio = 25.5;
entero cantidad = 4;
entero x;
entero total;
x = 4 + 3 * 2;
x = (4 + 3) * 2;
total = precio * cantidad;
si (total > 100) {
    imprimir(total);
}
maximo(x, total);
"""

ERROR = "entero y;\ny = ;\n"


def main():
    while True:
        print("\n--- MiniComp ---")
        print("1) Escribir código   2) Cargar archivo .txt   3) Ejemplo del PDF")
        print("4) Pruebas mínimas   5) Prueba con error      0) Salir")
        op = input("Opción: ").strip()
        if op == "0":
            break
        elif op == "1":
            print("Escribe tu código (termina con una línea que diga FIN):")
            lineas = []
            while (l := input()).strip().upper() != "FIN":
                lineas.append(l)
            procesar("\n".join(lineas))
        elif op == "2":
            ruta = input("Ruta del archivo: ").strip()
            try:
                with open(ruta, encoding="utf-8") as f:
                    procesar(f.read())
            except OSError:
                print("[ERROR] No se pudo abrir el archivo.")
        elif op == "3":
            procesar(EJEMPLO)
        elif op == "4":
            procesar(PRUEBAS)
        elif op == "5":
            procesar(ERROR)
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()