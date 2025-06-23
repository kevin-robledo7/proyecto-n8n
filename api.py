from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

app = FastAPI()

class InputProyecto(BaseModel):
    ley_cobre: float
    ley_oro: float
    precio_cobre: float
    precio_oro: float
    toneladas: int
    costo_operativo: float
    inversion_inicial: float
    años: int
    estado_mercado: str
    oferta_comprador: float
    tasa_descuento: float

def calcular_ingresos(ley_cobre, ley_oro, precio_cobre, precio_oro, toneladas):
    cobre_lb = toneladas * ley_cobre / 100 * 2204.62
    oro_oz = toneladas * ley_oro / 31.1035
    return cobre_lb * precio_cobre + oro_oz * precio_oro

def calcular_van(flujos, tasa):
    return sum([flujo / (1 + tasa) ** t for t, flujo in enumerate(flujos)])

def calcular_tir(flujos):
    tasa_min, tasa_max, paso = -0.9, 1.5, 0.0001
    mejor_tasa, mejor_van = None, float('inf')
    for r in np.arange(tasa_min, tasa_max, paso):
        van = sum([flujo / (1 + r)**i for i, flujo in enumerate(flujos)])
        if abs(van) < abs(mejor_van):
            mejor_van = van
            mejor_tasa = r
    return mejor_tasa

def calcular_payback(flujos):
    acumulado = 0
    for i, f in enumerate(flujos[1:], 1):
        acumulado += f
        if acumulado + flujos[0] >= 0:
            return i
    return None

def decision_estrategica(van, tir, precio_metal, punto_eq, oferta, mercado):
    if van > 0 and mercado == "favorable":
        return "Expandir", "VAN positivo y mercado favorable."
    elif precio_metal < punto_eq:
        return "Suspender temporalmente", "Precio del metal bajo el punto de equilibrio."
    elif van < 0 and oferta > abs(van):
        return "Vender", "VAN negativo pero hay una oferta de compra favorable."
    elif van < 0 and tir < 0.08:
        return "Descontinuar", "Proyecto no rentable."
    else:
        return "Mantener en evaluación", "No se cumplen condiciones claras."

@app.post("/evaluar")
def evaluar(data: InputProyecto):
    ingreso = calcular_ingresos(data.ley_cobre, data.ley_oro, data.precio_cobre, data.precio_oro, data.toneladas)
    flujo_neto = ingreso - data.costo_operativo
    flujos = [-data.inversion_inicial] + [flujo_neto] * data.años
    van = calcular_van(flujos, data.tasa_descuento)
    tir = calcular_tir(flujos)
    payback = calcular_payback(flujos)
    precio_unit = ingreso / data.toneladas
    punto_eq = data.costo_operativo / data.toneladas
    decision, motivo = decision_estrategica(van, tir, precio_unit, punto_eq, data.oferta_comprador, data.estado_mercado)

    return {
        "ingreso_anual": ingreso,
        "van": van,
        "tir": tir,
        "payback": payback,
        "precio_unitario": precio_unit,
        "punto_equilibrio": punto_eq,
        "decision": decision,
        "motivo": motivo
    }
