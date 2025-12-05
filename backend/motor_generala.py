# backend/motor_generala.py
import random
import csv
import json
import os
from collections import Counter

# ---------- RUTAS DE ARCHIVOS ----------

# Carpeta donde está ESTE archivo (backend/)
_BASE_BACKEND = os.path.dirname(__file__)
# Carpeta raíz del proyecto (un nivel arriba)
_BASE_PROYECTO = os.path.dirname(_BASE_BACKEND)

RUTA_NIVELES = os.path.join(_BASE_BACKEND, "niveles.json")
RUTA_PUNTAJES = os.path.join(_BASE_PROYECTO, "data", "puntajes.csv")

# ---------- CONSTANTES LÓGICA BÁSICA ----------

CANT_DADOS = 5
TIROS_POR_RONDA = 3
PUNTOS_GENERALA_SERVIDA = 1000

CATEGORIAS_BASE = [
    "unos", "doses", "treses", "cuatros", "cincos", "seises",
    "escalera", "full", "poker", "generala"
]

# ---------- NIVELES / TEMÁTICA ----------

def cargar_niveles():
    """Lee el archivo niveles.json y devuelve la lista de niveles."""
    with open(RUTA_NIVELES, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["niveles"]

def simbolo_dado(nivel, valor):
    """Devuelve el texto temático para un valor de dado (1-6)."""
    return nivel["simbolos_dados"][valor - 1]

def nombre_categoria(nivel, categoria_base):
    """
    Devuelve el nombre renombrado de la categoría (temático),
    o la base si no está renombrada.
    """
    return nivel["categorias"].get(categoria_base, categoria_base)

def puntos_especiales(nivel, categoria_base):
    """Devuelve los puntos para escalera/full/poker/generala según el nivel."""
    especiales = nivel.get("puntos_especiales", {})
    # Valores por defecto si no están en el JSON
    default = {
        "escalera": 20,
        "full": 30,
        "poker": 40,
        "generala": 50
    }
    return especiales.get(categoria_base, default.get(categoria_base, 0))

# ---------- ESTADO DE PARTIDA ----------

def crear_estado_partida():
    """Crea el estado inicial de una partida."""
    return {
        "puntajes": {cat: None for cat in CATEGORIAS_BASE},
        "dados": [0] * CANT_DADOS,
        "tiros_restantes": TIROS_POR_RONDA,
        "categorias_restantes": set(CATEGORIAS_BASE),
        "generala_servida": False
        
    }

# ---------- LÓGICA DE DADOS ----------

def tirar_dados(estado, indices_a_conservar=None):
    """
    Modifica el estado tirando los dados que NO estén en indices_a_conservar.
    indices_a_conservar es una lista de posiciones 0-4.
    """
    if indices_a_conservar is None:
        indices_a_conservar = []

    # Guardamos cuántos tiros quedaban ANTES de tirar
    tiros_antes = estado["tiros_restantes"]

    nuevos_dados = []
    for i in range(CANT_DADOS):
        if i in indices_a_conservar:
            nuevos_dados.append(estado["dados"][i])
        else:
            nuevos_dados.append(random.randint(1, 6))

    estado["dados"] = nuevos_dados

    # --- DETECCIÓN DE GENERALA SERVIDA ---[6,6,6,6,6]
    # Solo si es el PRIMER tiro de la ronda
    if tiros_antes == TIROS_POR_RONDA:
        if len(set(estado["dados"])) == 1:  # los 5 dados iguales
            estado["generala_servida"] = True
        else:
            estado["generala_servida"] = False

    # Descontamos el tiro
    estado["tiros_restantes"] -= 1


# ---------- DETECCIÓN DE JUGADAS ----------

def es_escalera(dados):
    ordenados = sorted(dados)
    return ordenados == [1,2,3,4,5] or ordenados == [2,3,4,5,6]

def es_full(dados):
    c = Counter(dados).values()
    return sorted(c) == [2,3]

def es_poker(dados):
    return 4 in Counter(dados).values()

def es_generala(dados):
    return 5 in Counter(dados).values()

# ---------- PUNTAJES ----------

def puntaje_categoria(dados, categoria, nivel):
    c = Counter(dados)

    if categoria == "unos":
        return c[1] * 1
    if categoria == "doses":
        return c[2] * 2
    if categoria == "treses":
        return c[3] * 3
    if categoria == "cuatros":
        return c[4] * 4
    if categoria == "cincos":
        return c[5] * 5
    if categoria == "seises":
        return c[6] * 6

    if categoria == "escalera" and es_escalera(dados):
        return puntos_especiales(nivel, "escalera")
    if categoria == "full" and es_full(dados):
        return puntos_especiales(nivel, "full")
    if categoria == "poker" and es_poker(dados):
        return puntos_especiales(nivel, "poker")
    if categoria == "generala" and es_generala(dados):
        return puntos_especiales(nivel, "generala")

    # Si no se logra la jugada, 0 puntos
    return 0

def posibles_puntajes(estado, nivel):
    """Devuelve {categoria: puntaje_posible} para las categorías libres."""
    dados = estado["dados"]
    res = {}
    for cat in estado["categorias_restantes"]:
        res[cat] = puntaje_categoria(dados, cat, nivel)
    return res

def anotar_categoria(estado, categoria, nivel):
    """Anota la categoría y prepara la próxima ronda."""
    # Si es generala y fue servida (primer tiro con 5 iguales) -> 1000 puntos
    if categoria == "generala" and estado.get("generala_servida", False):
        puntos = PUNTOS_GENERALA_SERVIDA
    else:
        puntos = puntaje_categoria(estado["dados"], categoria, nivel)

    estado["puntajes"][categoria] = puntos
    estado["categorias_restantes"].remove(categoria)

    # Reseteamos para la próxima ronda
    estado["tiros_restantes"] = TIROS_POR_RONDA
    estado["dados"] = [0] * CANT_DADOS
    estado["generala_servida"] = False   # ya se usó o se descartó

    return puntos

def puntaje_total(estado):
    return sum(p for p in estado["puntajes"].values() if p is not None)

# ---------- CSV DE PUNTAJES ----------

def guardar_puntaje(nombre, puntos):
    """Guarda nombre y puntos en el CSV."""
    os.makedirs(os.path.dirname(RUTA_PUNTAJES), exist_ok=True)

    with open(RUTA_PUNTAJES, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([nombre, puntos])

def leer_top10():
    """Lee los puntajes del CSV y devuelve los 10 mejores."""
    if not os.path.exists(RUTA_PUNTAJES):
        return []

    puntajes = []
    with open(RUTA_PUNTAJES, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for fila in reader:
            if len(fila) != 2:
                continue
            nombre, puntos = fila
            try:
                puntos = int(puntos)
            except ValueError:
                continue
            puntajes.append((nombre, puntos))

    puntajes.sort(key=lambda x: x[1], reverse=True)
    return puntajes[:10]
