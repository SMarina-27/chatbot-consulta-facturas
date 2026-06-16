# 🤖 Chatbot — Consulta de Estado de Pagos a Proveedores

**Trabajo Práctico Integrador — Organización Empresarial**  
Tecnicatura Universitaria en Programación (TUP) — UTN  
Cátedra: Prof. Gabriela Martínez  
Autores: Silvia Vargas y Dario Monzon  
Año: 2026

---

## 📋 Descripción

Sistema de consulta automatizada que permite a proveedores de una empresa
verificar el estado de pago de sus facturas a través de un chatbot de consola.

El sistema fue diseñado siguiendo la metodología **BPMN 2.0**, implementando
una **Máquina de Estados Finita** y consultando una **base de datos simulada**
en formato CSV mediante la librería **pandas**.

---

## 🗂️ Estructura del proyecto

```
📁 chatbot-proveedores/
│
├── chatbot_proveedores.py     ← Código principal del chatbot
├── proveedores.csv            ← Base de datos de proveedores
├── facturas.csv               ← Base de datos de facturas
├── README.md                  ← Este archivo
│
└── 📁 documentacion/
    ├── Modelo_BPMN_ChatBot_consulta_proveedor.png
    ├── maquina_estados_chatbot_consulta_proveedores.xlsx
    └── diccionario_datos_chatbot.xlsx
```

---

## ⚙️ Requisitos

- Python 3.8 o superior
- Librería pandas

### Instalación de dependencias

```bash
pip install pandas
```

---

## 🚀 Cómo ejecutar

1. Clonar el repositorio:

```bash
git clone https://github.com/SMarina-27/chatbot-consulta-facturas.git
cd chatbot-proveedores
```

2. Instalar dependencias:

```bash
pip install pandas
```

3. Ejecutar el chatbot:

```bash
python chatbot_proveedores.py
```

> Los archivos `proveedores.csv` y `facturas.csv` deben estar
> en la misma carpeta que `chatbot_proveedores.py`.

---

## 💬 Cómo usar el chatbot

Al iniciar, el bot solicita el **CUIT** del proveedor y luego el
**número de factura** a consultar. El flujo completo es:

```
──────────────────────────────────────────────────────
  SISTEMA DE CONSULTAS — Innovatech S.A.
  Chatbot de estado de pagos a proveedores
──────────────────────────────────────────────────────

🤖  Hola, ingrese su CUIT sin guiones.
👤  Su CUIT: 30111111111

    [CUIT válido → Ferretería La Tuerca S.R.L.]

🤖  CUIT verificado. Ingrese número de factura.
👤  Número de factura: 1001

    [Factura encontrada → consultando estado...]
    [Consultando base de datos...]

🤖  Factura N° 1001 — Estado: PAGADA ✅
    Descripción  : Ladrillo
    Monto        : $45,000.00
    Fecha de pago: 05/06/2025

🤖  ¿Desea consultar otra factura? (Sí/No)
👤  Su respuesta: No

🤖  Esperamos haber resuelto su consulta. ¡Hasta pronto!
```

---

## 🗃️ Base de datos simulada

### proveedores.csv

| Campo        | Tipo    | Descripción                                  |
|--------------|---------|----------------------------------------------|
| cuit         | VARCHAR | CUIT del proveedor (11 dígitos, sin guiones) |
| razon_social | VARCHAR | Nombre legal o comercial                     |
| email        | VARCHAR | Correo electrónico de contacto               |
| telefono     | VARCHAR | Teléfono de contacto                         |
| activo       | BOOLEAN | Sí = puede consultar / No = dado de baja     |

> **Nota sobre CUITs argentinos:**
> Personas jurídicas (SA, SRL): prefijo **30**
> Personas humanas masculino: prefijo **20**
> Personas humanas femenino: prefijo **27**

### facturas.csv

| Campo          | Tipo    | Descripción                                      |
|----------------|---------|--------------------------------------------------|
| nro_factura    | INTEGER | Número único de factura (clave primaria)         |
| cuit_proveedor | VARCHAR | CUIT del proveedor emisor (clave foránea)        |
| descripcion    | VARCHAR | Descripción del bien o servicio facturado        |
| monto          | DECIMAL | Importe total en pesos argentinos                |
| fecha_emision  | DATE    | Fecha de emisión (DD/MM/AAAA)                    |
| estado         | VARCHAR | PAGADA / PENDIENTE / RECHAZADA                   |
| fecha_pago     | DATE    | Fecha de pago efectivo (solo si estado = PAGADA) |
| motivo_rechazo | VARCHAR | Motivo (solo si estado = RECHAZADA)              |

---

## 🔄 Máquina de Estados

El bot implementa los siguientes estados:

| Estado               | Descripción                                      |
|----------------------|--------------------------------------------------|
| `ESPERANDO_CUIT`     | Estado inicial — solicita CUIT al proveedor      |
| `ERROR_CUIT`         | CUIT inválido — ofrece reintento (máx. 3)        |
| `ESPERANDO_FACTURA`  | CUIT validado — solicita número de factura       |
| `ERROR_FACTURA`      | Factura inválida — ofrece reintento (máx. 3)     |
| `CONSULTANDO_BD`     | Proceso interno — lee facturas.csv               |
| `MOSTRAR_PAGADA`     | Muestra monto y fecha de pago                    |
| `MOSTRAR_PENDIENTE`  | Informa que la factura está en revisión          |
| `MOSTRAR_RECHAZADA`  | Informa motivo de rechazo                        |
| `PREGUNTAR_CONTINUAR`| Ofrece consultar otra factura                    |
| `FIN`                | Cierra la sesión                                 |

---

## 🛡️ Manejo de errores (Camino Infeliz)

El sistema contempla los siguientes casos de error:

### Errores de CUIT
| Caso                        | Respuesta del bot                                  |
|-----------------------------|----------------------------------------------------|
| Contiene letras o símbolos  | "El CUIT debe contener solo números"               |
| Menos o más de 11 dígitos   | "El CUIT debe tener 11 dígitos. Usted ingresó N"   |
| No existe en el sistema     | "CUIT no encontrado. Verifique e intente"          |
| Proveedor dado de baja      | "Proveedor dado de baja. Contáctese con Admin."    |
| 3 intentos fallidos         | Sesión finalizada automáticamente                  |

### Errores de Factura
| Caso                        | Respuesta del bot                                  |
|-----------------------------|----------------------------------------------------|
| Contiene letras o símbolos  | "El número de factura debe ser numérico"           |
| No existe en el sistema     | "Factura no encontrada. Verifique el número"       |
| Pertenece a otro proveedor  | "Esa factura no corresponde al CUIT ingresado"     |
| 3 intentos fallidos         | Sesión finalizada automáticamente                  |

---

## 🏗️ Arquitectura y tecnologías

| Componente      | Tecnología          | Justificación                                      |
|-----------------|---------------------|----------------------------------------------------|
| Lenguaje        | Python 3            | Versátil, sintaxis clara, ideal para prototipos    |
| Datos           | pandas + CSV        | Simula base de datos sin infraestructura adicional |
| Modelado        | BPMN 2.0 (Bizagi)   | Estándar internacional de modelado de procesos     |
| Plataforma      | Consola (stdin)     | Portable, sin dependencias de red                  |
| Control de vers.| GitHub              | Trazabilidad del desarrollo                        |

---

## 📄 Documentación incluida

- **Diagramas BPMN 2.0** — flujo completo del proceso con carriles Usuario/Bot
- **Máquina de Estados** — tabla con los 10 estados, transiciones y mensajes
- **Diccionario de Datos** — entidades, atributos, tipos y validaciones

---

## 📚 Datos de prueba

Para probar el sistema podés usar los siguientes datos de los CSV:

| CUIT        | Proveedor                   | Facturas disponibles                              |
|-------------|-----------------------------|---------------------------------------------------|
| 30111111111 | Ferretería La Tuerca S.R.L. | 1001 (PAGADA), 1002 (PENDIENTE), 1004 (RECHAZADA) |
| 30222222222 | Papeleria La Hoja S.A.      | 1003 (PAGADA), 1007 (RECHAZADA)                   |
| 20333333333 | Gómez Bolaños Roberto       | 1005 (PENDIENTE), 1006 (PAGADA)                   |
| 20444444444 | Edgar Vivar                 | *(dado de baja — acceso denegado)*                |
