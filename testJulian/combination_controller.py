from itertools import combinations

def obtener_posiciones(letras, cadena_numerica, expresion=""):
    #print(letras, cadena_numerica)
    indices_letras = [expresion.find(letra) if expresion.find(letra) != -1 else None for letra in letras]
    posiciones_cadena = ''.join([cadena_numerica[pos] for pos in indices_letras if pos < len(cadena_numerica)])
    return posiciones_cadena


def divide_expression(expression):
    print("Expresion: " ,expression)
    numerador, denominador = expression.split('|')

    if '=' not in denominador:
        return []
    denominador, valor_numerico = denominador.split('=')
    all_combinations = list()

    for i in range(len(numerador) + 1):
        for numerador_part in combinations(numerador, i):
            numerador_remainder = ''.join([char for char in numerador if char not in numerador_part])

            for j in range(len(denominador) + 1):
                for denominador_part in combinations(denominador, j):
                    denominador_remainder = ''.join([char for char in denominador if char not in denominador_part])
                    combined_expression = list()
                    denominador_part_sub = ''.join(denominador_part)
                    combined_expression.append(f"{''.join(numerador_part)}|{ denominador_part_sub + '=' + obtener_posiciones(denominador_part_sub, valor_numerico, denominador) if len(denominador_part) > 0 else denominador_part_sub}")
                    #print(len(''.join(denominador_part)), ''.join(denominador_part), combined_expression)
                    combined_expression.append(f"{numerador_remainder}|{denominador_remainder + '=' + obtener_posiciones(denominador_remainder, valor_numerico, denominador) if len(denominador_remainder) > 0 else denominador_remainder}")
                    if '|' != combined_expression[0] and '|' != combined_expression[1] and [combined_expression[0],combined_expression[1]] not in all_combinations and [combined_expression[1],combined_expression[0]] not in all_combinations:
                        all_combinations.append(combined_expression)
    #''.join(denominador_part) + '=' + obtener_posiciones(''.join(denominador_part), valor_numerico)
    return all_combinations

""" expression = "C|AC=10" #BC = (1,(0,0)) BC|BC=00 y 0/A=1
combinations = divide_expression(expression)

for i, combo in enumerate(combinations, start=1):
    print(f"{i}. {combo}") """
