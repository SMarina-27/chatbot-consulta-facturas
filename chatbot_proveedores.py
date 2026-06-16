# =============================================================
# CHATBOT — Consulta de Estado de Pagos a Proveedores
# Municipio — Organización Empresarial TPI 2025
# =============================================================
# Este código fue generado a partir de los siguientes documentos
# de diseño provistos por el equipo:
#   - Diagrama BPMN 2.0 (Bizagi Modeler)
#   - Máquina de Estados (maquina_estados_chatbot_consulta_proveedores.xlsx)
#   - Diccionario de Datos (diccionario_datos_chatbot.xlsx)
#   - Base de datos simulada (proveedores.csv, facturas.csv)
#
# Dependencias: pip install pandas
# Uso: python chatbot_proveedores.py
#      (proveedores.csv y facturas.csv deben estar en la misma carpeta)
#
# NOTA — CUITs argentinos:
#   Personas jurídicas (SA, SRL, etc.) → prefijo 30
#   Personas humanas masculino         → prefijo 20
#   Personas humanas femenino          → prefijo 27
#   Todos tienen exactamente 11 dígitos sin guiones.
# =============================================================

import pandas as pd

# -------------------------------------------------------------
# CONSTANTES
# Surgen del Diccionario de Datos (hoja Atributos,
# sección Variables de Sesión).
# -------------------------------------------------------------
PROVEEDORES_CSV  = "proveedores.csv"
FACTURAS_CSV     = "facturas.csv"
MAX_INTENTOS     = 3        # límite de reintentos (CUIT y factura)
SEPARADOR        = "─" * 54

# -------------------------------------------------------------
# CARGA DE DATOS CON PANDAS
# dtype=str garantiza que los campos clave (cuit, nro_factura)
# se lean como texto y no como enteros, evitando errores de
# comparación con el input del usuario.
# Fuente: Diccionario de Datos — cuit: VARCHAR 11 dígitos
#                               nro_factura: INTEGER (se trata como str)
# -------------------------------------------------------------
def cargar_datos():
    proveedores = pd.read_csv(
        PROVEEDORES_CSV,
        dtype={"cuit": str}
    )
    facturas = pd.read_csv(
        FACTURAS_CSV,
        dtype={"nro_factura": str, "cuit_proveedor": str}
    )
    # Eliminar espacios en blanco en campos clave
    proveedores["cuit"]        = proveedores["cuit"].str.strip()
    facturas["nro_factura"]    = facturas["nro_factura"].str.strip()
    facturas["cuit_proveedor"] = facturas["cuit_proveedor"].str.strip()
    return proveedores, facturas

# -------------------------------------------------------------
# SESIÓN — memoria del bot
# Variables definidas en Diccionario de Datos,
# hoja Atributos, sección "VARIABLES DE SESIÓN"
# -------------------------------------------------------------
def nueva_sesion():
    return {
        "estado":           "ESPERANDO_CUIT",  # str   — estado actual (máquina de estados)
        "cuit":             None,              # str   — CUIT validado del proveedor
        "nro_factura":      None,              # str   — número de factura validado
        "intentos_cuit":    0,                 # int   — contador errores CUIT (máx. 3)
        "intentos_factura": 0,                 # int   — contador errores factura (máx. 3)
        "resultado":        None,              # dict  — fila completa de facturas.csv
    }

# -------------------------------------------------------------
# SALIDA POR CONSOLA
# -------------------------------------------------------------
def bot(msg):
    """Imprime un mensaje del sistema/bot."""
    print(f"\n🤖  {msg}")

def sistema(msg):
    """Imprime un mensaje interno del sistema (proceso)."""
    print(f"    [{msg}]")

# -------------------------------------------------------------
# VALIDACIONES — camino infeliz (Unhappy Path)
# Cada función retorna (ok: bool, mensaje: str, datos: dict|None)
# Los casos de error surgen del BPMN y del Diccionario de Datos.
# -------------------------------------------------------------

def validar_cuit(entrada, proveedores):
    """
    Valida el CUIT ingresado por el usuario contra proveedores.csv.

    Caminos de error cubiertos (gateway ¿CUIT Válido? del BPMN):
      A) Contiene caracteres no numéricos
      B) Longitud distinta de 11 dígitos
      C) No existe en proveedores.csv
      D) El proveedor existe pero está dado de baja (activo = 'No')
    """
    cuit = entrada.strip().replace("-", "").replace(" ", "")

    # A — no numérico
    if not cuit.isdigit():
        return False, "⚠️  El CUIT debe contener solo números (sin guiones ni espacios).", None

    # B — longitud incorrecta
    if len(cuit) != 11:
        return False, f"⚠️  El CUIT debe tener 11 dígitos. Usted ingresó {len(cuit)}.", None

    # C — buscar en DataFrame (gateway BPMN: ¿CUIT Válido?)
    fila = proveedores[proveedores["cuit"] == cuit]
    if fila.empty:
        return False, "⚠️  CUIT no encontrado en el sistema. Verifique e intente nuevamente.", None

    # D — proveedor inactivo
    proveedor = fila.iloc[0]
    if str(proveedor["activo"]).strip() == "No":
        return False, "⚠️  Proveedor dado de baja. Contáctese con Administración.", None

    return True, "", proveedor.to_dict()


def validar_factura(entrada, cuit, facturas):
    """
    Valida el número de factura ingresado contra facturas.csv.

    Caminos de error cubiertos (gateway ¿Factura Existe? del BPMN):
      A) Contiene caracteres no numéricos
      B) No existe en facturas.csv
      C) Existe pero pertenece a otro proveedor (distinto CUIT)
    """
    nro = entrada.strip()

    # A — no numérico
    if not nro.isdigit():
        return False, "⚠️  El número de factura debe ser numérico. Intente nuevamente.", None

    # B — buscar en DataFrame (gateway BPMN: ¿Factura Existe?)
    fila = facturas[facturas["nro_factura"] == nro]
    if fila.empty:
        return False, "⚠️  Factura no encontrada. Verifique el número e intente nuevamente.", None

    # C — factura de otro proveedor
    factura = fila.iloc[0]
    if factura["cuit_proveedor"] != cuit:
        return False, "⚠️  Esa factura no corresponde al CUIT ingresado. Verifique los datos.", None

    return True, "", factura.to_dict()

# -------------------------------------------------------------
# ESTADOS
# Una función por cada estado de la Máquina de Estados.
# Cada función retorna el nombre del estado siguiente.
# Mensajes tomados literalmente de la columna
# "Mensaje del bot" de la planilla de Máquina de Estados.
# -------------------------------------------------------------

def estado_esperando_cuit(sesion, proveedores):
    """
    Estado: ESPERANDO_CUIT
    Acción: Solicita CUIT del proveedor (11 dígitos)
    Transición OK  → ESPERANDO_FACTURA
    Transición Err → ERROR_CUIT
    """
    bot("Hola, ingrese su CUIT sin guiones.")
    entrada = input("👤  Su CUIT: ").strip()
    ok, msg, proveedor = validar_cuit(entrada, proveedores)
    if ok:
        sesion["cuit"]          = proveedor["cuit"]
        sesion["intentos_cuit"] = 0
        sistema(f"CUIT válido → {proveedor['razon_social']}")
        return "ESPERANDO_FACTURA"
    sesion["intentos_cuit"] += 1
    bot(msg)
    if sesion["intentos_cuit"] >= MAX_INTENTOS:
        bot("Superó el número máximo de intentos. La sesión ha finalizado.")
        return "FIN"
    print(f"    (Intento {sesion['intentos_cuit']} de {MAX_INTENTOS})")
    return "ERROR_CUIT"


def estado_error_cuit(sesion, proveedores):
    """
    Estado: ERROR_CUIT
    Acción: Solicita reingresar CUIT válido
    Transición OK  → ESPERANDO_FACTURA
    Transición Err → ERROR_CUIT (reintento)
    """
    bot("CUIT no encontrado. Verifique e intente nuevamente.")
    entrada = input("👤  Su CUIT: ").strip()
    ok, msg, proveedor = validar_cuit(entrada, proveedores)
    if ok:
        sesion["cuit"]          = proveedor["cuit"]
        sesion["intentos_cuit"] = 0
        sistema(f"CUIT válido → {proveedor['razon_social']}")
        return "ESPERANDO_FACTURA"
    sesion["intentos_cuit"] += 1
    bot(msg)
    if sesion["intentos_cuit"] >= MAX_INTENTOS:
        bot("Superó el número máximo de intentos. La sesión ha finalizado.")
        return "FIN"
    print(f"    (Intento {sesion['intentos_cuit']} de {MAX_INTENTOS})")
    return "ERROR_CUIT"


def estado_esperando_factura(sesion, facturas):
    """
    Estado: ESPERANDO_FACTURA
    Acción: Solicita número de factura
    Transición OK  → CONSULTANDO_BD
    Transición Err → ERROR_FACTURA
    """
    bot("CUIT verificado. Ingrese número de factura.")
    entrada = input("👤  Número de factura: ").strip()
    ok, msg, factura = validar_factura(entrada, sesion["cuit"], facturas)
    if ok:
        sesion["nro_factura"]      = factura["nro_factura"]
        sesion["resultado"]        = factura
        sesion["intentos_factura"] = 0
        sistema("Factura encontrada → consultando estado...")
        return "CONSULTANDO_BD"
    sesion["intentos_factura"] += 1
    bot(msg)
    if sesion["intentos_factura"] >= MAX_INTENTOS:
        bot("Superó el número máximo de intentos. La sesión ha finalizado.")
        return "FIN"
    print(f"    (Intento {sesion['intentos_factura']} de {MAX_INTENTOS})")
    return "ERROR_FACTURA"


def estado_error_factura(sesion, facturas):
    """
    Estado: ERROR_FACTURA
    Acción: Solicita reingresar número de factura
    Transición OK  → CONSULTANDO_BD
    Transición Err → ERROR_FACTURA (reintento)
    """
    bot("Factura no encontrada. Verifique el número e intente nuevamente.")
    entrada = input("👤  Número de factura: ").strip()
    ok, msg, factura = validar_factura(entrada, sesion["cuit"], facturas)
    if ok:
        sesion["nro_factura"]      = factura["nro_factura"]
        sesion["resultado"]        = factura
        sesion["intentos_factura"] = 0
        sistema("Factura encontrada → consultando estado...")
        return "CONSULTANDO_BD"
    sesion["intentos_factura"] += 1
    bot(msg)
    if sesion["intentos_factura"] >= MAX_INTENTOS:
        bot("Superó el número máximo de intentos. La sesión ha finalizado.")
        return "FIN"
    print(f"    (Intento {sesion['intentos_factura']} de {MAX_INTENTOS})")
    return "ERROR_FACTURA"


def estado_consultando_bd(sesion):
    """
    Estado: CONSULTANDO_BD
    Acción: Ejecuta lectura de CSV, determina estado del pago
    Transición → MOSTRAR_PAGADA / MOSTRAR_PENDIENTE / MOSTRAR_RECHAZADA
    (gateway ¿Estado? del BPMN)
    """
    sistema("Consultando base de datos...")
    estado = sesion["resultado"]["estado"]
    if   estado == "PAGADA":    return "MOSTRAR_PAGADA"
    elif estado == "PENDIENTE": return "MOSTRAR_PENDIENTE"
    elif estado == "RECHAZADA": return "MOSTRAR_RECHAZADA"
    else:
        bot("Estado desconocido. Contáctese con Administración.")
        return "FIN"


def estado_mostrar_pagada(sesion):
    """
    Estado: MOSTRAR_PAGADA
    Mensaje: Factura PAGADA — Monto y Fecha de pago
    Fuente campos: diccionario de datos — monto (DECIMAL), fecha_pago (DATE DD/MM/AAAA)
    Transición → PREGUNTAR_CONTINUAR
    """
    f = sesion["resultado"]
    bot(
        f"Factura N° {f['nro_factura']} — Estado: PAGADA ✅\n"
        f"    Descripción  : {f['descripcion']}\n"
        f"    Monto        : ${float(f['monto']):,.2f}\n"
        f"    Fecha de pago: {f['fecha_pago']}"
    )
    return "PREGUNTAR_CONTINUAR"


def estado_mostrar_pendiente(sesion):
    """
    Estado: MOSTRAR_PENDIENTE
    Mensaje: Factura PENDIENTE — en revisión
    Transición → PREGUNTAR_CONTINUAR
    """
    f = sesion["resultado"]
    bot(
        f"Factura N° {f['nro_factura']} — Estado: PENDIENTE ⏳\n"
        f"    Descripción  : {f['descripcion']}\n"
        f"    Monto        : ${float(f['monto']):,.2f}\n"
        f"    Su factura fue recibida y se encuentra en revisión."
    )
    return "PREGUNTAR_CONTINUAR"


def estado_mostrar_rechazada(sesion):
    """
    Estado: MOSTRAR_RECHAZADA
    Mensaje: Factura RECHAZADA — motivo de rechazo
    Fuente campo: diccionario de datos — motivo_rechazo (VARCHAR)
    Transición → PREGUNTAR_CONTINUAR
    """
    f = sesion["resultado"]
    bot(
        f"Factura N° {f['nro_factura']} — Estado: RECHAZADA ❌\n"
        f"    Descripción      : {f['descripcion']}\n"
        f"    Monto            : ${float(f['monto']):,.2f}\n"
        f"    Motivo de rechazo: {f['motivo_rechazo']}\n"
        f"    Contáctese con el área de Administración."
    )
    return "PREGUNTAR_CONTINUAR"


def estado_preguntar_continuar(sesion):
    """
    Estado: PREGUNTAR_CONTINUAR
    Acción: Pregunta si desea consultar otra factura
    Transición Sí → ESPERANDO_FACTURA (mantiene CUIT en sesión)
    Transición No → FIN
    """
    bot("¿Desea consultar otra factura? (Sí/No)")
    respuesta = input("👤  Su respuesta: ").strip().lower()
    if respuesta in ("si", "sí", "s", "yes", "y"):
        # Resetea datos de factura, mantiene CUIT (decisión de diseño BPMN)
        sesion["nro_factura"]      = None
        sesion["resultado"]        = None
        sesion["intentos_factura"] = 0
        return "ESPERANDO_FACTURA"
    return "FIN"


def estado_fin():
    """
    Estado: FIN
    Mensaje: Esperamos haber resuelto su consulta. Hasta pronto.
    """
    bot("Esperamos haber resuelto su consulta. ¡Hasta pronto!")
    print(f"\n{SEPARADOR}\n")

# -------------------------------------------------------------
# BUCLE PRINCIPAL — Motor de la Máquina de Estados
# Implementa la tabla de despacho: estado → función
# Corresponde al flujo completo del diagrama BPMN.
# -------------------------------------------------------------
def ejecutar_chatbot():
    proveedores, facturas = cargar_datos()

    print(f"\n{SEPARADOR}")
    print("  SISTEMA DE CONSULTAS — MUNICIPIO")
    print("  Chatbot de estado de pagos a proveedores")
    print(f"{SEPARADOR}")

    sesion = nueva_sesion()

    while sesion["estado"] != "FIN":
        e = sesion["estado"]
        if   e == "ESPERANDO_CUIT":      sesion["estado"] = estado_esperando_cuit(sesion, proveedores)
        elif e == "ERROR_CUIT":          sesion["estado"] = estado_error_cuit(sesion, proveedores)
        elif e == "ESPERANDO_FACTURA":   sesion["estado"] = estado_esperando_factura(sesion, facturas)
        elif e == "ERROR_FACTURA":       sesion["estado"] = estado_error_factura(sesion, facturas)
        elif e == "CONSULTANDO_BD":      sesion["estado"] = estado_consultando_bd(sesion)
        elif e == "MOSTRAR_PAGADA":      sesion["estado"] = estado_mostrar_pagada(sesion)
        elif e == "MOSTRAR_PENDIENTE":   sesion["estado"] = estado_mostrar_pendiente(sesion)
        elif e == "MOSTRAR_RECHAZADA":   sesion["estado"] = estado_mostrar_rechazada(sesion)
        elif e == "PREGUNTAR_CONTINUAR": sesion["estado"] = estado_preguntar_continuar(sesion)
        else:
            bot("Error inesperado. Reiniciando sesión.")
            sesion = nueva_sesion()

    estado_fin()

# -------------------------------------------------------------
if __name__ == "__main__":
    ejecutar_chatbot()
