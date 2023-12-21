from copy import copy, deepcopy
import numpy as np
from pprint import pprint
import combination_controller as cc

combinaciones_evaluadas = dict()

def eliminar_duplicados(fila):
    lista_sin_duplicados = [item for i, item in enumerate(fila) if item not in fila[:i]]
    return lista_sin_duplicados


def generar_diccionario(letra_final):
    diccionario = {}
    letra_final = letra_final.upper()
    if ord(letra_final) < ord("C"):
        letra_final = "C"
    for i in range(ord("A"), ord(letra_final) + 1):
        diccionario[chr(i)] = i - ord("A")

    return diccionario


def procesar_cadena(cadena):
    # Definir el mapeo de caracteres a números
    copy_cadena = cadena[:]
    cadena_si_or = copy_cadena.replace("|", "")
    mapeo = generar_diccionario(max(cadena_si_or, key=ord))
    # Dividir la cadena en partes
    partes = cadena.split("|")

    # Obtener el estado futuro, estado actual y valor del estado actual
    estado_futuro = [mapeo[c] for c in partes[0]]
    #print(len(partes[1]))
    estado_actual = []
    valor_estado_actual = []
    if len(partes[1]) > 0:
        estado_actual = [mapeo[c] for c in partes[1].split("=")[0]]
        valor_estado_actual = [int(digito) for digito in partes[1].split("=")[1]]
    else:
        estado_actual = []

    # Calcular las letras que faltan en estado actual y futuro
    letras_faltantes_actual = [i for i in range(len(mapeo)) if i not in estado_actual]
    letras_faltantes_futuro = [i for i in range(len(mapeo)) if i not in estado_futuro]

    if len(letras_faltantes_actual) == len(mapeo):
        letras_faltantes_actual = []
    if len(letras_faltantes_futuro) == len(mapeo):
        letras_faltantes_futuro = []

    return letras_faltantes_futuro, letras_faltantes_actual, valor_estado_actual


def mariginalizar_estado_actual(matriz, channel, position=0):
    """
    Entrada:
        matriz: Una matriz en formato especial, donde cada fila tiene una lista de canales y valores asociados.
        channel: Una lista que representa los canales (0 para A, 1 para B, 2 para C).
        position (opcional): Un índice que indica el canal actual que se está marginalizando
        (por defecto, comienza desde el canal A).
    Salida: Una nueva matriz marginalizada después de eliminar el canal especificado.
    """
    # Verificar que el canal especificado sea válido
    if position > len(channel) - 1:
        return matriz
    if channel[position] not in [0, 1, 2]:
        raise ValueError("Canal no válido. Debe ser 0 para A, 1 para B o 2 para C.")
    copy_matriz = copy(matriz)
    # Inicializar la matriz marginalizada con ceros
    marginalized_matriz = []

    # Iterar sobre cada fila de la matriz original
    for row in copy_matriz:
        if row[0] != "" and len(row[0]) > channel[position]:
            row[0].remove(row[0][channel[position]])
        marginalized_matriz.append(row)
    matriz_sum_rows = sumar_filas(marginalized_matriz)
    return mariginalizar_estado_actual(matriz_sum_rows, channel, position + 1)


def mariginalizar_estado_futuro(matriz, canales, posicion=0):
    if posicion > len(canales) - 1:
        return matriz
    if canales[posicion] not in [0, 1, 2]:
        return ValueError("Canal no valido")
    copy_matriz = copy(matriz)
    fila_canales = copy_matriz[0]
    nueva_fila_canales = [""]

    for canal in fila_canales:
        if len(canal) > 0:
            canal.remove(canal[canales[posicion]])
            nueva_fila_canales.append(canal)
    copy_matriz.insert(0, nueva_fila_canales)
    matriz_marginalizada = sumar_columnas(copy_matriz[1:])
    return mariginalizar_estado_futuro(matriz_marginalizada, canales, posicion + 1)


def sumar_filas(matriz, columnas=False):
    """
    Entrada: Una matriz en formato especial, donde cada fila tiene una clave (canal) y valores asociados.
    Salida: Una nueva matriz después de sumar las filas con la misma clave.
    """
    resultado = {}
    copia_matriz = copy(matriz)

    for fila in copia_matriz:
        clave = tuple(fila[0])
        if clave in resultado:
            if not columnas:
                resultado[clave] = [
                    round((a + b) / 2, 2) for a, b in zip(resultado[clave], fila[1:])
                ]
            else:
                resultado[clave] = [
                    round(a + b, 2) for a, b in zip(resultado[clave], fila[1:])
                ]
        else:
            resultado[clave] = fila[1:]

    matriz_resultado = [
        [[int(x) for x in key], *values] for key, values in resultado.items()
    ]
    return matriz_resultado


def sumar_columnas(matriz):
    # Obtener el número de filas y columnas
    num_filas = len(matriz)
    num_columnas = len(matriz[0])

    # Crear la nueva matriz intercambiando filas con columnas
    nueva_matriz = [
        [matriz[j][i] for j in range(num_filas)] for i in range(num_columnas)
    ]

    suma_col = intercambiar_filas_columnas(sumar_filas(nueva_matriz, columnas=True))

    return suma_col


def producto_tensor(matriz):
    # limpiar la matriz para poder operar sobre ella
    matriz_subproblemas = []
    for vector in matriz:
        matriz_subproblemas.append(vector[1:][0][1:])

    # Verifica que la matriz tenga al menos dos vectores
    if len(matriz) < 2 or len(matriz_subproblemas) < 2:
        raise ValueError("La matriz debe contener al menos dos vectores.")

    # Calcula el producto tensor de los dos primeros vectores
    resultado = np.kron(matriz_subproblemas[0], matriz_subproblemas[1])

    # Calcula el producto tensor de los vectores restantes
    for i in range(2, len(matriz_subproblemas)):
        resultado = np.kron(resultado, matriz_subproblemas[i])

    return resultado


def convertir_cadena_a_lista(cadena):
    """
    Entrada: Una cadena que representa una lista de valores numéricos encerrados en corchetes y separados por comas. Ejemplo: "[1, 2, 3]"
    Salida: Una lista de enteros obtenida al convertir la cadena de entrada.
    """
    return [int(char) for char in cadena[1:-1].split()]


def intercambiar_filas_columnas(matriz):
    # Obtener el número de filas y columnas
    num_filas = len(matriz)
    num_columnas = len(matriz[0])

    # Crear la nueva matriz intercambiando filas con columnas
    nueva_matriz = [
        [matriz[j][i] for j in range(num_filas)] for i in range(num_columnas)
    ]

    return nueva_matriz


def convertir_matriz(matriz):
    """
    Entrada: Una matriz en formato especial, donde cada fila tiene una lista de canales y valores asociados.
    Salida: Una nueva matriz donde las cadenas de canales se convierten en listas de enteros, y los valores
    se convierten en números de punto flotante.
    """
    copy_matriz = copy(matriz)
    new_matriz = []
    for fila in copy_matriz:
        new_matriz.append(
            [convertir_cadena_a_lista(fila[0])] + [float(valor) for valor in fila[1:]]
        )

    return new_matriz


def extraer_probabildad_estado_canal_actual(matriz=[], cadena=""):
    if cadena == "" or len(matriz) == 0:
        return []

    copy_matriz = deepcopy(matriz)
    encabezados = copy_matriz[0]
    _, _, valor_estado_actual = procesar_cadena(cadena=cadena)
    probabilidades_estado_futuro = []
    if len(valor_estado_actual) > 0:
        probabilidades_estado_futuro = [
            fila for fila in copy_matriz if fila[0] == valor_estado_actual
        ]
        probabilidades_estado_futuro.insert(0, encabezados)
        return probabilidades_estado_futuro
    cabecera = copy_matriz[0]
    nueva_matriz = intercambiar_filas_columnas(copy_matriz)
    catidad_estados = len(nueva_matriz[0]) - 1
    sumar_filas = [
        [[]]
        + [round((sum(fila[1:]) / catidad_estados), 2) for fila in nueva_matriz[1:]]
    ]
    sumar_filas.insert(0, cabecera)

    return sumar_filas


def obtener_combinaciones(cadena):
    # Dividir la cadena en dos partes: la primera parte antes del '|' y la segunda parte después del '='
    partes = cadena.split("|")
    prefijo = partes[0]
    sufijo_valor = partes[1]

    # Dividir la segunda parte en dos: la parte antes del '=' y la parte después del '='
    sufijo, valor = sufijo_valor.split("=")

    # Crear la lista de combinaciones
    combinaciones = [f"{caracter}|{sufijo}={valor}" for caracter in prefijo]

    return combinaciones


def marginalizacion_producto_tensor(matriz=[], combinaciones=[]):
    if len(matriz) < 1:
        return []
    if len(combinaciones) < 1:
        return []
    copy_matriz = deepcopy(matriz)
    matriz_operar = deepcopy(copy_matriz)
    matriz_resultado = []

    for probabilidad in combinaciones:
        #marginalizacion_producto_tensor(matriz_operar, probabilidad)
        matriz_resultado.append(generar_probabilidad(matriz_operar, probabilidad))
        matriz_operar = deepcopy(copy_matriz)
        """ if isinstance(probabilidad, list) and len(probabilidad):
            marginalizacion_producto_tensor(matriz_operar, cc.divide_expression(probabilidad[0]))
            marginalizacion_producto_tensor(matriz_operar, cc.divide_expression(probabilidad[1])) """
    return matriz_resultado

def generar_probabilidad(matriz, probabilidad):

    if  probabilidad in combinaciones_evaluadas:
        print("*****************************************************************")
        return combinaciones_evaluadas[probabilidad]
    
    matriz_operar = deepcopy(matriz)
    m_estado_futuro, m_estado_actual, _ = procesar_cadena(probabilidad)
    m_margi_estado_actual = mariginalizar_estado_actual(
        matriz_operar, m_estado_actual[::-1]
    )
    m_margi_estado_futuro = mariginalizar_estado_futuro(
        m_margi_estado_actual, m_estado_futuro[::-1]
    )
    extraer_probabilidad = extraer_probabildad_estado_canal_actual(
        m_margi_estado_futuro, probabilidad
    )
    combinaciones_evaluadas[probabilidad] = extraer_probabilidad[1:][0][1:]
    return extraer_probabilidad