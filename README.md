# MiniComp

**Generador de código intermedio** desarrollado para la Unidad 2 de *Lenguajes y Autómatas II*.

MiniComp lee un programa escrito en un mini lenguaje en español y produce la tabla de símbolos, las notaciones infija/prefija/postfija, los **cuádruplos** y los **triplos** correspondientes.

---

## Características

- Analizador léxico basado en expresiones regulares
- Verificación de balance de paréntesis `()` y llaves `{}`
- Analizador sintáctico por **descenso recursivo** (respeta precedencia y paréntesis)
- Tabla de símbolos con tipo y valor inicial, y registro de constantes
- Conversión de expresiones a notación **infija, prefija y postfija**
- Generación de **cuádruplos** y **triplos**, con temporales (`t1`, `t2`...) y etiquetas (`L1`, `L2`...)
- Mensajes de error con número de línea
- Menú interactivo en consola

---

## Flujo del compilador

```mermaid
flowchart LR
    A[Código fuente] --> B[Análisis léxico<br/>tokenizar]
    B --> C[Verificar balance<br/>( ) y { }]
    C --> D[Análisis sintáctico<br/>descenso recursivo]
    D --> E[Tabla de símbolos]
    D --> F[Notaciones<br/>infija / prefija / postfija]
    D --> G[Cuádruplos]
    D --> H[Triplos]
```

---

## Lenguaje soportado

| Elemento | Sintaxis | Ejemplo |
|---|---|---|
| Declaración | `entero` / `decimal` | `entero a = 8;` `decimal p = 2.5;` `entero r;` |
| Asignación | `id = expresión;` | `r = a + b * 2;` |
| Condicional | `si (cond) { ... }` | `si (r > 10) { r = r - 1; }` |
| Llamadas | `función(args);` | `imprimir(r);` `maximo(a, b);` |
| Operadores | `+  -  *  /` y `( )` | `(4 + 3) * 2` |
| Comparadores | `<  >  <=  >=  ==  !=` | `a != b` |

**Funciones predefinidas**

| Función | Parámetros |
|---|---|
| `imprimir` | 1 |
| `cuadrado` | 1 |
| `maximo` | 2 |

**Precedencia de operadores:** `*` y `/` (mayor) → `+` y `-` (menor).

---

## Requisitos

- Python **3.8 o superior** (usa el operador `:=`)
- No requiere librerías externas

---

## Uso

```bash
python MiniComp.py
```

Se mostrará el siguiente menú:

```
--- MiniComp ---
1) Escribir código   2) Cargar archivo .txt   3) Ejemplo del PDF
4) Pruebas mínimas   5) Prueba con error      0) Salir
```

| Opción | Descripción |
|---|---|
| 1 | Escribes tu propio código; termina con una línea que diga `FIN` |
| 2 | Carga un archivo de texto con tu programa |
| 3 | Ejecuta el ejemplo base |
| 4 | Ejecuta un conjunto de pruebas mínimas (decimales, paréntesis, funciones) |
| 5 | Muestra cómo se reporta un error |
| 0 | Salir |

---

## Ejemplo

**Entrada**

```
entero a = 8;
entero b = 3;
entero resultado;
resultado = a + b * 2;
si (resultado > 10) {
    resultado = resultado - 1;
}
imprimir(resultado);
```

**Salida**

```
====================================================
 1. TABLA DE SÍMBOLOS
====================================================
Identificador  Tipo      Valor inicial
a              entero    8
b              entero    3
resultado      entero    -
Constantes: 8, 3, 2, 10, 1

====================================================
 2. NOTACIONES
====================================================
Infija : a + b * 2
Prefija: + a * b 2
Postfija: a b 2 * +

Infija : resultado - 1
Prefija: - resultado 1
Postfija: resultado 1 -

====================================================
 3. CUÁDRUPLOS
====================================================
(1) (=, 8, -, a)
(2) (=, 3, -, b)
(3) (*, b, 2, t1)
(4) (+, a, t1, t2)
(5) (=, t2, -, resultado)
(6) (>, resultado, 10, t3)
(7) (IF_FALSE, t3, -, L1)
(8) (-, resultado, 1, t4)
(9) (=, t4, -, resultado)
(10) (LABEL, -, -, L1)
(11) (PARAM, resultado, -, -)
(12) (CALL, imprimir, 1, -)

====================================================
 4. TRIPLOS
====================================================
(1) (=, 8, a)
(2) (=, 3, b)
(3) (*, b, 2)
(4) (+, a, (3))
(5) (=, (4), resultado)
(6) (>, resultado, 10)
(7) (IF_FALSE, (6), L1)
(8) (-, resultado, 1)
(9) (=, (8), resultado)
(10) (LABEL, L1)
(11) (PARAM, resultado)
(12) (CALL, imprimir, 1)
```

### Ejemplo de error

**Entrada**

```
entero y;
y = ;
```

**Salida**

```
[ERROR] Línea 2: asignación sin expresión
```

---

## Errores detectados

- Símbolos no admitidos
- Paréntesis o llaves sin pareja
- Identificadores no declarados o declarados dos veces
- Falta de `;`, `=`, `(`, `)` o `{`
- Asignaciones sin expresión
- Expresiones incompletas
- Funciones no definidas o con número incorrecto de parámetros

---

## Estructura del código

| Sección | Descripción |
|---|---|
| `tokenizar` / `verificar_balance` | Análisis léxico y balance de delimitadores |
| `prefija` / `postfija` / `unir_infija` | Conversión de notaciones a partir del árbol de la expresión |
| `class MiniComp` | Parser y generador de código intermedio |
| `procesar` / `main` | Presentación de resultados y menú de consola |

---

## Limitaciones

- No hay verificación de tipos (`entero` vs `decimal`)
- Solo existe el condicional `si` (sin `sino` ni ciclos)
- Las funciones disponibles son fijas (`imprimir`, `cuadrado`, `maximo`)
- No ejecuta el programa; solo genera el código intermedio

---

## Autor

Proyecto académico — Instituto Tecnológico de Zitácuaro (TecNM)
Lenguajes y Autómatas II — Unidad 2
