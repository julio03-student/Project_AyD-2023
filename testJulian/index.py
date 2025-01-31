"""import pyphi
import numpy as np



tmp = [[0,0,0],[0,0,1],[1,0,1],[1,0,0],[1,1,0],[1,1,1],[1,1,1],[1,1,0]]
cm=np.array([[0,0,1],[1,0,1],[1,1,0]])
labels = ['A','B','C']
network = pyphi.Network(tmp,cm=cm,node_labels=labels)
state = (1,0,0)
subsystem = pyphi.Subsystem(network, state)

x = pyphi.compute.phi(subsystem)
phi = x.phi
mip=x.cut
t=x.time

print('MIP: ', mip, 'PHI: ', phi, 'TIME: ', t ) """

from copy import deepcopy
import pyphi
import numpy as np
from itertools import product
from fractions import Fraction
from pprint import pprint
import time
import prettytable
import pandas as pd
import marginalization as mg
import combination_controller as cc
from scipy.stats import wasserstein_distance

# Realizado por Julián Rivera Castaño y Juan Felipe Cortes Castrillon


# Genera un conjunto de muestras aleatorias
def generar_muestras1(n_muestras, n_canales):
    muestras = np.random.randint(2, size=(n_muestras, n_canales))
    return muestras


def generar_muestras(archivo_excel):
    df = pd.read_excel(archivo_excel)
    columnas_seleccionadas = df.iloc[2:, 1:4]

    return columnas_seleccionadas.to_numpy()


def custom_order(tupla):
    return (tupla[2], tupla[1], tupla[0])


# Crea un diccionario para clave valor para almacencar sus respectivos valores
def inicializar_diccionario(n_canales):
    combinaciones = list(product([0, 1], repeat=n_canales))

    combinaciones = sorted(combinaciones, key=custom_order)

    transiciones = {
        combo: {chr(65 + j): 0 for j in range(n_canales)} for combo in combinaciones
    }
    for combo in transiciones:
        transiciones[combo]["repetidos"] = 0
    return transiciones


# Cuenta cuando existe un 1 en el canal y suma, y cuenta cuantos veces se repite
# cada fila
def generar_matriz_estado_canal_F(muestras, transiciones):
    n_muestras = len(muestras)

    for i in range(n_muestras - 1):
        estado_actual = tuple(muestras[i])
        estado_siguiente = tuple(muestras[i + 1])

        transiciones[estado_actual]["repetidos"] += 1

        for canal in range(n_canales):
            if estado_siguiente[canal] == 1:
                transiciones[estado_actual][chr(65 + canal)] += 1


# Cuenta cuando existe un 1 en el canal y suma, y cuenta cuantos veces se repite
# cada fila anterior
def generar_matriz_estado_canal_P(muestras, transiciones):
    n_muestras = len(muestras)
    for i in range(n_muestras - 1):
        estado_actual = tuple(muestras[i])
        estado_anterior = tuple(muestras[i - 1])

        transiciones[estado_actual]["repetidos"] += 1

        for canal in range(n_canales):
            if estado_anterior[canal] == 1:
                transiciones[estado_actual][chr(65 + canal)] += 1


# Calcula y agrega el valor de la probabilidad de que exista un uno en el
# siguente estado en el canal
def calcular_probabilidades(transiciones):
    for info in transiciones.values():
        for canal in range(n_canales):
            if info["repetidos"] > 0:
                fraccion = Fraction(info[chr(65 + canal)], info["repetidos"])
                info[chr(65 + canal)] = str(round(float(fraccion), 2))
            else:
                info[chr(65 + canal)] = "0"


def calcular_probabilidades_estado(transiciones, info):
    dict = list(info.values())

    for index in range(len(transiciones)):
        for chr in range(1, len(transiciones[index])):
            if transiciones[index][chr] != 0:
                fraccion = Fraction(transiciones[index][chr], dict[index]["repetidos"])
                transiciones[index][chr] = str(
                    # Fraction(transiciones[index][chr], dict[index]["repetidos"]).evalf()
                    round(float(fraccion), 2)
                )
            else:
                transiciones[index][chr] = "0"


def imprimir_transiciones(transiciones):
    # Obtener todas las claves de los canales (que son letras del alfabeto)
    canales = sorted(
        set(c for info in transiciones.values() for c in info.keys() if c.isalpha())
    )

    # Crear una tabla con las columnas de estado, repetidos y los canales.
    table = prettytable.PrettyTable(["Estado", *canales])

    # Agregar los datos a la tabla.
    for estado, info in transiciones.items():
        estado_str = "".join(map(str, estado))
        row_data = [estado_str]
        for canal in canales:
            row_data.append(info.get(canal, "0/1"))  # Usar '0/1' si la clave no existe
        table.add_row(row_data)

    data = list(transiciones.values())

    matriz = [
        [float(diccionario["A"]), float(diccionario["B"]), float(diccionario["C"])]
        for diccionario in data
    ]

    # Imprime la matriz

    pyphi.config.load_file("pyphi_config.yml")

    tpm = np.array(matriz)

    cm = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])

    labels = ("A", "B", "C")

    network = pyphi.Network(tpm, cm=cm, node_labels=labels)
    state = (1, 1, 0)

    subsystem = pyphi.Subsystem(network, state)

    x = pyphi.compute.sia(subsystem)

    phi = x.phi
    mip = x.cut
    t = x.time

    # Imprimir la tabla.
    print(table.get_string())

    print("MIP: ", mip, "PHI: ", phi, "TIME:", t)


# Retorna cuantas veces está filA después de filaB
def contador_a_respecto_b(filaA, filaB, lista):
    contador = 0
    for i in range(len(lista) - 1):
        if lista[i] == filaA and lista[i + 1] == filaB:
            contador += 1
    return contador


# Genera la matriz de estado estado F
def generar_matriz_estado_estado_F(estados, transiciones):
    lista_coincidencias = []
    for fila in range(len(estados)):
        fila_coincidencias = []
        fila_coincidencias.append(estados[fila])
        for filaS in range(len(estados)):
            fila_coincidencias.append(
                contador_a_respecto_b(estados[fila], estados[filaS], transiciones)
            )
        lista_coincidencias.append(fila_coincidencias)
    return lista_coincidencias


# Genera la matriz de estado estado P
def generar_matriz_estado_estado_P(estados, transiciones):
    lista_coincidencias = []
    for fila in range(len(estados)):
        fila_coincidencias = []
        fila_coincidencias.append(estados[fila])
        for filaS in range(len(estados)):
            fila_coincidencias.append(
                contador_a_respecto_b(estados[filaS], estados[fila], transiciones)
            )
        lista_coincidencias.append(fila_coincidencias)
    return lista_coincidencias


def generar_estados(numero_canales):
    matriz = [
        [int(bit) for bit in format(i, f"0{numero_canales}b")]
        for i in range(2**numero_canales)
    ]
    matriz_invertida = [list(reversed(fila)) for fila in matriz]
    matriz_invertida.insert(0, "")

    return matriz_invertida


# A partir de un diccionario, retorna una lista de strings
def pasar_dict_a_array_str(lista):
    array = np.array(list(lista))
    return [str(fila) for fila in array]


# Imprime una matriz con encabezados en consola
def imprimir_matriz(matriz, encabezados):
    copia_list = encabezados.copy()
    copia_list.insert(0, " ")
    tablaM = prettytable.PrettyTable(copia_list)

    for fila in matriz:
        tablaM.add_row(fila)

    print(tablaM)


def imprimir_matriz_marginalizada(matriz):
    tabla = prettytable.PrettyTable(matriz[0])

    for fila in matriz[1:]:
        tabla.add_row(fila)

    print(tabla)


def combinaciones_marginalizacion_completa(
    combinaciones=[], matriz_estado=[], cadena="", marginalizacion_generica=[]
):
    copy_matriz_estado = deepcopy(matriz_estado)
    valores_emb_combinaciones = {}
    for combinacion in combinaciones:
        print("COMBINACION: ", combinacion)
        # combinaciones_marginalizacion_completa(cc.divide_expression(combinacion), copy_matriz_estado, cadena, marginalizacion_generica)

        lista_de_probabilidades = mg.marginalizacion_producto_tensor(
            copy_matriz_estado, combinacion
        )

        for x in lista_de_probabilidades:
            imprimir_matriz_marginalizada(x)

        resultado_producto_tensor = mg.producto_tensor(lista_de_probabilidades)

        print(f"EL RESULTADO DEL PRODUCTO TENSOR DE {combinacion} es:")
        print(resultado_producto_tensor)

        print(f"EL RESULTADO DE LA POBABILIDAD GENERICA {cadena} es:")
        print(marginalizacion_generica[1:][0][1:])

        emd = wasserstein_distance(
            resultado_producto_tensor, marginalizacion_generica[1:][0][1:]
        )
        valores_emb_combinaciones[str(combinacion)] = emd
        print(f"La distancia de transporte es: {emd}")
    return valores_emb_combinaciones


if __name__ == "__main__":
    start_time = time.time()  # Registra el tiempo de inicio
    n_muestras = 10
    n_canales = 3

    # muestras = generar_muestras(n_muestras, n_canales)
    muestras = generar_muestras(archivo_excel="Muestra17-18.xlsx")
    print("____________Muestras________________")
    print(muestras.T)

    estado_canal_f = inicializar_diccionario(n_canales)
    estado_canal_p = inicializar_diccionario(n_canales)
    estado_estado_f = inicializar_diccionario(n_canales)
    estado_estado_p = inicializar_diccionario(n_canales)

    # EstadoCanalF
    print("___________ESTADOCANALF_____________")
    generar_matriz_estado_canal_F(muestras, estado_canal_f)
    calcular_probabilidades(estado_canal_f)
    imprimir_transiciones(estado_canal_f)

    # print(estado_canal_f)
    # EstadoCanalP
    print("___________ESTADOCANALP_____________")
    generar_matriz_estado_canal_P(muestras, estado_canal_p)
    calcular_probabilidades(estado_canal_p)
    imprimir_transiciones(estado_canal_p)

    muestras_str = [str(fila) for fila in muestras]
    lista_estados = pasar_dict_a_array_str(estado_estado_f.keys())

    # EstadoEstadoF
    print("___________ESTADOESTADOF_____________")
    matriz_estado_f = generar_matriz_estado_estado_F(lista_estados, muestras_str)
    calcular_probabilidades_estado(matriz_estado_f, estado_canal_f)
    imprimir_matriz(matriz_estado_f, lista_estados)

    # EstadoEstadoP
    print("___________ESTADOESTADOP_____________")
    matriz_estado_p = generar_matriz_estado_estado_P(lista_estados, muestras_str)
    calcular_probabilidades_estado(matriz_estado_p, estado_canal_p)
    imprimir_matriz(matriz_estado_p, lista_estados)

    # Marginalizacion estado actual
    cadena1 = "BC|AC=10"
    m_estado_futuro, m_estado_actual, v_estado_actual = mg.procesar_cadena(cadena1)
    copy_matriz_estado = mg.convertir_matriz(matriz_estado_f.copy())
    copy_matriz_estado.insert(0, generar_estados(n_canales))
    pprint

    print("___________MATRIZ MARGINALIZADA EN ESTADO ACTUAL_____________")
    print("ESTADOS A ELIMINAR: ", m_estado_actual)
    matriz_marginalizada_estado_actual = mg.mariginalizar_estado_actual(
        copy_matriz_estado, m_estado_actual[::-1]
    )
    imprimir_matriz_marginalizada(matriz_marginalizada_estado_actual)

    print("___________MATRIZ MARGINALIZADA EN ESTADO FUTURO_____________")
    print("ESTADOS FUTUROS A ELIMINAR ", m_estado_futuro)
    matriz_marginlizada_estado_futuro = mg.mariginalizar_estado_futuro(
        matriz_marginalizada_estado_actual, m_estado_futuro[::-1]
    )
    imprimir_matriz_marginalizada(matriz_marginlizada_estado_futuro)

    print("___________EXTRAER PROBABILIDAD EN ESTADO ACTUAL_____________")

    probabilidades_segun_cadena = mg.extraer_probabildad_estado_canal_actual(
        matriz=matriz_marginlizada_estado_futuro, cadena=cadena1
    )
    # probabilidades_segun_cadena.insert(0, generar_estados(n_canales))
    imprimir_matriz_marginalizada(probabilidades_segun_cadena)

    print("________________________PRODUCTO TENSOR______________________")
    cadena2 = "ABC|ABC=111"
    copy_matriz_estado = mg.convertir_matriz(matriz_estado_f.copy())
    copy_matriz_estado.insert(0, generar_estados(n_canales))
    """ combinaciones = mg.obtener_combinaciones(cadena2)
    print("Antes")
    pprint(combinaciones) """
    combinaciones = cc.divide_expression(cadena2)
    print("Antes")
    pprint(combinaciones)

    # print("Prueba", copy_matriz_estado, cadena2)

    marginalizacion_generica = mg.generar_probabilidad(copy_matriz_estado, cadena2)
    print("----------------VALORES EMB--------------------------")
    valors_emb = combinaciones_marginalizacion_completa(
        combinaciones, copy_matriz_estado, cadena2, marginalizacion_generica
    )
    """ for combinacion in combinaciones[::-1]:
        lista_de_probabilidades = mg.marginalizacion_producto_tensor(
            copy_matriz_estado, combinacion
        )

        for x in lista_de_probabilidades:
            imprimir_matriz_marginalizada(x)

        resultado_producto_tensor = mg.producto_tensor(lista_de_probabilidades)

        print(f"EL RESULTADO DEL PRODUCTO TENSOR DE {combinacion} es:")
        print(resultado_producto_tensor)

        print(f"EL RESULTADO DE LA POBABILIDAD GENERICA {cadena2} es:")
        print(marginalizacion_generica[1:][0][1:])

        emd = wasserstein_distance(resultado_producto_tensor, marginalizacion_generica[1:][0][1:])
        print(f"La distancia de transporte es: {emd}") """

    print("_________________________")
    print("COMBINACIONES EVALUADAS")
    pprint(mg.combinaciones_evaluadas)

    """ print("COMBINACIONES:", combinaciones)
    lista_de_probabilidades = mg.marginalizacion_producto_tensor(
        copy_matriz_estado, combinaciones
    )
    for x in lista_de_probabilidades:
        imprimir_matriz_marginalizada(x)

    resultado_producto_tensor = mg.producto_tensor(lista_de_probabilidades)

    print(f"EL RESULTADO DEL PRODUCTO TENSOR DE {cadena2} es:")
    print(resultado_producto_tensor)
 """
    # cc.extraer_valor_optimo(mg.combinaciones_evaluadas, combinaciones)
    end_time = time.time()  # Registra el tiempo de finalización
    # Calcula el tiempo transcurrido en segundos
    elapsed_time = end_time - start_time
    print(f"Tiempo de ejecución: {elapsed_time:.6f} segundos")
