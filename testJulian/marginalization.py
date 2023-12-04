import numpy as np
import re

def marginalization_base(intruction, matriz_estado_f, estados):
    intruction1 = intruction.split('|')
    state_future = intruction1[0].split('=') #Lista estados futuros [A,B,....] = [1,0,...]
    state_current = intruction1[1].split('=') #lista estados actuales [A,B,....] = [1,0,...]

    print(intruction)
    state_future_str, state_current_str = extraer_estados(intruction, state_current[0])

    print(state_current[0], state_future[0], state_future_str, state_current_str)

    new_data = [[float(val) for val in sublist[1:]] for sublist in matriz_estado_f] # Lista de listas de los valores de la matriz de estados futuros


    positions = [ord(state) - ord('A') for state in state_current[0]] #Lista posición de los estados futuros [0,2]

    nuevos_estados = [tuple(map(int, s.strip('[]').split())) for s in estados] #Lista de tuplas de los estados futuros [(0,0),(0,1),(1,0),(1,1)]

    print(nuevos_estados)
    print(positions)

    nuevas_tuplas = [tuple(tupla[pos] for pos in positions) for tupla in nuevos_estados] #Lista de tuplas de los estados futuros [(0,0),(0,1),(1,0),(1,1)]
    print(nuevas_tuplas)

    #unique_tuplas = sorted(list(set(nuevas_tuplas)), key=lambda x: (x[1], x[0]))

    unique_tuplas = sorted(list(set(nuevas_tuplas)), key=lambda x: tuple(reversed(x))) #lista de tuplas únicas [(0,0),(0,1),(1,0),(1,1)]

    print(unique_tuplas)

    #Marginalización de cada estado futuro con respecto a los estados actuales
    resultado = np.array([sum_columns_(new_data, tupla, nuevas_tuplas) for tupla in unique_tuplas]) 

    print(resultado.T) 


#Permite convertir una lista de enteros a una cadena de caracteres
def convert_state(state):
    lista_digitos = [int(digito) for digito in state]
    return "[" + " ".join(map(str, lista_digitos)) + "]"

def marginalization_base2(cadena):
    # Utiliza una expresión regular para encontrar todos los números en la cadena
    intruction = re.findall(r'\d+', cadena)
    
    # Convierte los números en la lista a enteros utilizando NumPy
    states = np.array(list(map(int, intruction)))
    
    # Separa los números en dos arrays
    future_state = states[::2]  # Primer número (índices pares)
    past_state = states[1::2]  # Segundo número (índices impares)

    return future_state, past_state

def extraer_estados(cadena, estado_actual=None, estado_futuro=None):
    # Utiliza expresiones regulares para encontrar los números en la cadena
    if estado_actual and estado_futuro:
        matches = re.findall(fr'{estado_actual}=(\d+)\|{estado_futuro}=(\d+)', cadena)
        if matches:
            estado_actual_str, estado_futuro_str = matches[0]
            estado_actual_array = np.array([int(digito) for digito in estado_actual_str])
            estado_futuro_array = np.array([int(digito) for digito in estado_futuro_str])
            return estado_futuro_array, estado_actual_array
    elif estado_actual:
        matches = re.findall(fr'{estado_actual}=(\d+)', cadena)
        if matches:
            estado_actual_str = matches[0]
            estado_actual_array = np.array([int(digito) for digito in estado_actual_str])
            return [], estado_actual_array
    
    print(f"No se encontraron coincidencias para los estados {estado_actual} y {estado_futuro}.")
    return None

#suma columnas dado un estado
def sum_columns_(data, tuplaIndice, estados):

    indices_columnas = []

    # Obtener los índices de las columnas que cumplen la condición  
    for i, tupla in enumerate(estados):
        if tupla == tuplaIndice:
            indices_columnas.append(i)

    # Obtener las columnas que cumplen la condición
    columnas_condicion = [[tupla[pos] for pos in indices_columnas] for tupla in data]

    # Sumar las columnas seleccionadas
    columna_resultante = [round(sum(column),2) for column in columnas_condicion]

    return columna_resultante


"""
    Entrada: Una cadena cadena que representa estados y valores numéricos separados por |.
        Ejemplo: "AB=100|ABC=111"
    Salida: Una tupla de dos listas, donde la primera lista contiene las posiciones de las 
        letras faltantes en el estado actual, y la segunda lista contiene las posiciones de las
        letras faltantes en el estado futuro. Si no hay letras faltantes, 
        las listas correspondientes estarán vacías.
"""
def extraer_posiciones(cadena):
    posiciones_actual = []
    posiciones_futuro = []

    match = re.match(r'([A-Za-z]+)=([0-9]+)\|([A-Za-z]+)=([0-9]+)', cadena)

    if match:
        estado_actual, _, estado_futuro, _ = match.groups()

        for char in estado_actual:
            if char.isalpha():
                posiciones_actual.append(ord(char.upper()) - ord('A'))

        for char in estado_futuro:
            if char.isalpha():
                posiciones_futuro.append(ord(char.upper()) - ord('A'))

        letras_faltantes_actual = set(estado_futuro.upper()) - set(estado_actual.upper())
        letras_faltantes_futuro = set(estado_actual.upper()) - set(estado_futuro.upper())

        posiciones_faltantes_actual = [ord(char) - ord('A') for char in letras_faltantes_actual]
        posiciones_faltantes_futuro = [ord(char) - ord('A') for char in letras_faltantes_futuro]

        return posiciones_faltantes_actual, posiciones_faltantes_futuro

    return posiciones_actual, posiciones_futuro

"""
    Entrada:
        matrix: Una matriz en formato especial, donde cada fila tiene una lista de canales y valores asociados.
        channel: Una lista que representa los canales (0 para A, 1 para B, 2 para C).
        position (opcional): Un índice que indica el canal actual que se está marginalizando 
        (por defecto, comienza desde el canal A).
    Salida: Una nueva matriz marginalizada después de eliminar el canal especificado.
"""
def marginalize_matrix(matrix, channel, position=0):
    # Verificar que el canal especificado sea válido
    if position > len(channel) - 1:
        return matrix
    if channel[position] not in [0, 1, 2]:
        raise ValueError("Canal no válido. Debe ser 0 para A, 1 para B o 2 para C.")
    copy_matrix = matrix.copy()
    # Inicializar la matriz marginalizada con ceros
    marginalized_matrix = []

    # Iterar sobre cada fila de la matriz original
    for row in copy_matrix:
        if row[0]:
           row[0].remove(row[0][channel[position]])
        marginalized_matrix.append(row)
    matrix_sum_rows = sumar_filas(marginalized_matrix)
    return marginalize_matrix(matrix_sum_rows, channel, position+1)

"""
    Entrada: Una matriz en formato especial, donde cada fila tiene una clave (canal) y valores asociados.
    Salida: Una nueva matriz después de sumar las filas con la misma clave.
"""    
def sumar_filas(matriz):
    resultado = {}

    for fila in matriz:
        clave = tuple(fila[0])
        if clave in resultado:
            resultado[clave] = [round(a + b, 2) for a, b in zip(resultado[clave], fila[1:])]
        else:
            resultado[clave] = fila[1:]

    matriz_resultado = [[[int(x) for x in key], *values] for key, values in resultado.items()]
    return matriz_resultado

"""
    Entrada: Una cadena que representa una lista de valores numéricos encerrados en corchetes y separados por comas. Ejemplo: "[1, 2, 3]"
    Salida: Una lista de enteros obtenida al convertir la cadena de entrada.
"""
def convertir_cadena_a_lista(cadena):
    return [int(char) for char in cadena[1:-1].split()]

"""
    Entrada: Una matriz en formato especial, donde cada fila tiene una lista de canales y valores asociados.
    Salida: Una nueva matriz donde las cadenas de canales se convierten en listas de enteros, y los valores 
    se convierten en números de punto flotante.
"""
def convertir_matrix(matrix):
    new_matrix = []
    for fila in matrix:
        new_matrix.append([convertir_cadena_a_lista(fila[0])] + [float(valor) for valor in fila[1:]])

    return new_matrix



