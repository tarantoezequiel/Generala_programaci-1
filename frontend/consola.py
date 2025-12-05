from backend.motor_generala import (
    cargar_niveles,
    crear_estado_partida,
    tirar_dados,
    posibles_puntajes,
    anotar_categoria,
    puntaje_total,
    CATEGORIAS_BASE,
    simbolo_dado,
    nombre_categoria,
    guardar_puntaje,
    leer_top10,
)


# ---------- FUNCIONES DE IMPRESIÓN ----------

def mostrar_planilla(estado, nivel):
    # Calculamos los nombres de las categorías con la temática
    nombres_categorias = [nombre_categoria(nivel, cat) for cat in CATEGORIAS_BASE]

    # Ancho de la columna de categoría = lo que mida la más larga + 2 de margen
    ancho_cat = max(len("CATEGORIA"), *(len(n) for n in nombres_categorias)) + 2
    ancho_pts = 7  # columna de puntos

    # Fila superior
    print("╔" + "═" * ancho_cat + "╦" + "═" * ancho_pts + "╗")

    # Encabezados
    print(f"║{'CATEGORIA':^{ancho_cat}}║{'PUNTOS':^{ancho_pts}}║")

    # Separador
    print("╠" + "═" * ancho_cat + "╬" + "═" * ancho_pts + "╣")

    # Contenido
    for cat, nombre_mostrar in zip(CATEGORIAS_BASE, nombres_categorias):
        valor = estado["puntajes"][cat]
        texto = "-" if valor is None else str(valor)
        print(f"║{nombre_mostrar:<{ancho_cat}}║{texto:^{ancho_pts}}║")

    # Separador antes del total
    print("╠" + "═" * ancho_cat + "╬" + "═" * ancho_pts + "╣")

    # Total
    total = puntaje_total(estado)
    print(f"║{'TOTAL':<{ancho_cat}}║{total:^{ancho_pts}}║")

    # Fila inferior
    print("╚" + "═" * ancho_cat + "╩" + "═" * ancho_pts + "╝")



def mostrar_dados_ascii(estado, nivel):
    dados = estado["dados"]
    simbolos = [simbolo_dado(nivel, d) for d in dados]

    # Armamos las líneas de texto
    linea_valores = "Valores: " + "  ".join(str(d) for d in dados)
    linea_simbs   = "Tema   : " + " | ".join(simbolos)
    linea_tiros   = f"Tiros  : {estado['tiros_restantes']}"

    titulo = "DADOS ACTUALES"

    # Calculamos el ancho interior (sin bordes) según la línea más larga
    ancho = max(len(titulo), len(linea_valores), len(linea_simbs), len(linea_tiros))

    print()
    # Fila superior
    print("╔" + "═" * (ancho + 2) + "╗")
    # Título centrado
    print("║ " + titulo.center(ancho) + " ║")
    # Separador
    print("╠" + "═" * (ancho + 2) + "╣")
    # Contenido
    print("║ " + linea_valores.ljust(ancho) + " ║")
    print("║ " + linea_simbs.ljust(ancho) + " ║")
    print("║ " + linea_tiros.ljust(ancho) + " ║")
    # Fila inferior
    print("╚" + "═" * (ancho + 2) + "╝")


def pedir_indices_a_conservar():
    texto = input(
        "Ingrese posiciones de dados a conservar (1-5) separadas por coma, "
        "o ENTER para ninguno: "
    )
    if not texto.strip():
        return []
    try:
        posiciones = [int(x.strip()) - 1 for x in texto.split(",")]
    except ValueError:
        return []
    return [p for p in posiciones if 0 <= p < 5]

# ---------- FLUJO DE UNA PARTIDA ----------

def jugar_una_partida(nivel):
    estado = crear_estado_partida()

    while True:  # maneja esta partida completa
        # Si ya no quedan categorías, se terminó la partida normal
        if not estado["categorias_restantes"]:
            break

        # Cabecera "NUEVA RONDA"
        print("\n╔" + "═"*20 + "╗")
        print(f"║{'NUEVA RONDA':^20}║")
        print("╚" + "═"*20 + "╝")

        # Primer tiro de la ronda
        tirar_dados(estado, [])

        # --- CHEQUEO DE GENERALA SERVIDA LUEGO DEL PRIMER TIRO ---
        if estado.get("generala_servida", False):
            mostrar_planilla(estado, nivel)
            mostrar_dados_ascii(estado, nivel)

            puntos = anotar_categoria(estado, "generala", nivel)

            print("\n¡¡GENERALA SERVIDA!! ¡Ganaste automáticamente!")
            print(f"Te anotaste {puntos} puntos en '{nombre_categoria(nivel, 'generala')}'.")

            total = puntaje_total(estado)
            print("\n===== FIN DE LA PARTIDA =====")
            mostrar_planilla(estado, nivel)
            print(f"PUNTAJE FINAL: {total}")

            nombre = input("Ingrese su nombre para guardar el puntaje: ").strip() or "Anónimo"
            guardar_puntaje(nombre, total)
            print("Puntaje guardado en el archivo CSV.\n")

            seguir = input("¿Querés jugar otra partida? (s/n): ").strip().lower()
            if seguir == "s":
                estado = crear_estado_partida()
                continue
            else:
                return  # vuelve al menú principal

        # --- RONDA NORMAL (SIN GENERALA SERVIDA) ---
        while True:
            # SIEMPRE mostramos cómo están los dados ahora
            mostrar_planilla(estado, nivel)
            mostrar_dados_ascii(estado, nivel)

            # Si ya no quedan tiros, salimos del bucle
            if estado["tiros_restantes"] == 0:
                break

            op = input("Presione ENTER para tirar dados, o escriba S para salir de la partida: ").strip().lower()
            if op == "s":
                 print("Saliendo de la partida...\n")
                 return  # vuelve al menú principal
            
            indices = pedir_indices_a_conservar()
            tirar_dados(estado, indices)

        # Elegir categoría donde anotar
        print("\n╔" + "═"*30 + "╗")
        print(f"║{'POSIBLES JUGADAS':^30}║")
        print("╚" + "═"*30 + "╝")

        posibles = posibles_puntajes(estado, nivel)

        # Usamos el orden fijo de CATEGORIAS_BASE
        categorias_ordenadas = [cat for cat in CATEGORIAS_BASE if cat in posibles]

        for i, cat in enumerate(categorias_ordenadas, start=1):
            nombre_mostrar = nombre_categoria(nivel, cat)
            print(f"{i:2}) {nombre_mostrar:25} -> {posibles[cat]} puntos")

        while True:
            opcion = input("Seleccione el número de la categoría para anotar: ")
            if opcion.isdigit() and 1 <= int(opcion) <= len(categorias_ordenadas):
                cat_elegida = categorias_ordenadas[int(opcion) - 1]
                break
            print("Opción inválida.")

        puntos = anotar_categoria(estado, cat_elegida, nivel)
        print(f"\nAnotaste {puntos} puntos en '{nombre_categoria(nivel, cat_elegida)}'.")

    # Fin de partida normal (se llenaron todas las categorías)
    total = puntaje_total(estado)
    print("\n╔" + "═"*24 + "╗")
    print(f"║{'FIN DE LA PARTIDA':^24}║")
    print("╚" + "═"*24 + "╝")

    mostrar_planilla(estado, nivel)
    print(f"PUNTAJE FINAL: {total}")

    nombre = input("Ingrese su nombre para guardar el puntaje: ").strip() or "Anónimo"
    guardar_puntaje(nombre, total)
    print("Puntaje guardado en el archivo CSV.\n")

        # ----------- ELECCIÓN DE CATEGORÍA NORMAL -----------
    print("\n╔" + "═"*30 + "╗")
    print(f"║{'POSIBLES JUGADAS':^30}║")
    print("╚" + "═"*30 + "╝")

    posibles = posibles_puntajes(estado, nivel)
        # Orden fijo de categorías (la que definiste en CATEGORIAS_BASE)
    categorias_ordenadas = CATEGORIAS_BASE

    for i, cat in enumerate(categorias_ordenadas, start=1):
            if cat in posibles:
                nombre_mostrar = nombre_categoria(nivel, cat)
                print(f"{i:2}) {nombre_mostrar:25} -> {posibles[cat]} puntos")

    while True:
            opcion = input("Seleccione el número de la categoría para anotar (0 para salir): ")
            if opcion == "0":
                return  # salir de la partida
            if opcion.isdigit() and 1 <= int(opcion) <= len(categorias_ordenadas):
                cat_elegida = categorias_ordenadas[int(opcion) - 1]
                if cat_elegida in posibles:
                    break
            print("Opción inválida.")

    puntos = anotar_categoria(estado, cat_elegida, nivel)
    print(f"\nAnotaste {puntos} puntos en '{nombre_categoria(nivel, cat_elegida)}'.")

    # ----------- FINAL DE LA PARTIDA -----------
    if estado.get("generala_servida"):
        total = 1000
    else:
        total = puntaje_total(estado)

    print("\n╔" + "═"*24 + "╗")
    print(f"║{'FIN DE LA PARTIDA':^24}║")
    print("╚" + "═"*24 + "╝")

    mostrar_planilla(estado, nivel)
    print(f"PUNTAJE FINAL: {total}")

    nombre = input("Ingrese su nombre para guardar el puntaje: ").strip() or "Anónimo"
    guardar_puntaje(nombre, total)
    print("Puntaje guardado en el archivo CSV.\n")


# ---------- ESTADÍSTICAS Y CRÉDITOS ----------

def mostrar_estadisticas():
    top = leer_top10()

    print("\n╔" + "═"*26 + "╗")
    print(f"║{'TOP 10 PUNTAJES':^26}║")
    print("╚" + "═"*26 + "╝")

    if not top:
        print("Todavía no hay puntajes guardados.\n")
        return

    for i, (nombre, puntos) in enumerate(top, start=1):
        print(f"{i:2}) {nombre:15} - {puntos:4} pts")

    print()


def mostrar_creditos():
    print("\n########## MINI GENERALA TEMÁTICA ##########")
    print("Autores  : [Ezequiel Taranto / div 116]")
    print("Fecha    : Diciembre 2025")
    print("Materia  : Programación I")
    print("Docentes : [Martin Alejandro García y Carbonari Verónica]")
    print("Carrera  : Tecnicatura Universitaria en Programación")
    print("Contacto : tarantoezequiel47@gmail.com")
    print("###########################################\n")

# ---------- MENÚ PRINCIPAL ----------
def mostrar_menu_principal(nivel_actual):
    print("\n" + "╔" + "═"*35 + "╗")
    print(f"║{'MINI GENERALA':^35}║")
    print("║" + " "*35 + "║")
    print(f"║{nivel_actual['nombre']:^35}║")
    print("╠" + "═"*35 + "╣")
    print("║ 1) Jugar".ljust(36) + "║")
    print("║ 2) Estadísticas".ljust(36) + "║")
    print("║ 3) Créditos".ljust(36) + "║")
    print("║ 4) Salir".ljust(36) + "║")
    print("╚" + "═"*35 + "╝")

def menu_principal():
    niveles = cargar_niveles()
    nivel_actual = niveles[0]   # usamos el único nivel disponible
    
    while True:
        mostrar_menu_principal(nivel_actual)
        op = input("Seleccione una opción: ")

        if op == "1":
            jugar_una_partida(nivel_actual)
        elif op == "2":
            mostrar_estadisticas()
        elif op == "3":
            mostrar_creditos()
        elif op == "4":
            print("¡Gracias por jugar a Dragob Ball G!")
            break
        else:
            print("Seleccione una opción correcta.\n")

