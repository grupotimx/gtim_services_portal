from fastapi import FastAPI, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database import SessionLocal, engine
from models import Base, Llamada
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from typing import List, Optional
from datetime import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session

@app.get("/llamadas")
async def get_llamadas(
    fecha: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Llamada)
    if fecha:
        query = query.where(func.date(Llamada.fecha) == fecha)
    result = await db.execute(query)
    llamadas = result.scalars().all()

    return [
        {
            "record_id": l.record_id,
            "fecha": l.fecha.isoformat(),
            "estado": l.estado,
            "grupo_timbrado": l.grupo_timbrado,
            "duracion_seg": l.duracion_seg,
            "extension": l.extension
        }
        for l in llamadas
    ]

def obtener_turno(hora: time) -> str:
    if time(6, 0) <= hora <= time(13, 59):
        return "Matutino"
    elif time(14, 0) <= hora <= time(21, 59):
        return "Vespertino"
    else:
        return "Nocturno"

@app.get("/llamadas/stacked-por-turno")
async def llamadas_stacked_por_turno(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    grupo: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Llamada.fecha)

    if fecha_inicio:
        query = query.where(Llamada.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.where(Llamada.fecha <= fecha_fin)
    if grupo:
        query = query.where(Llamada.grupo_timbrado == grupo)

    result = await db.execute(query)
    fechas = result.scalars().all()

    agrupado = {}
    for fecha in fechas:
        dia_str = fecha.strftime('%a %Y-%m-%d')  # Ej: Wed 2025-06-26
        turno = obtener_turno(fecha.time())

        if dia_str not in agrupado:
            agrupado[dia_str] = {'Matutino': 0, 'Vespertino': 0, 'Nocturno': 0}
        agrupado[dia_str][turno] += 1

    labels = list(agrupado.keys())
    turnos = ['Matutino', 'Vespertino', 'Nocturno']
    colores = ['#007bff', '#28a745', '#ffc107']

    datasets = [
        {
            "label": turno,
            "data": [agrupado[fecha][turno] for fecha in labels],
            "backgroundColor": color
        }
        for turno, color in zip(turnos, colores)
    ]

    return {"labels": labels, "datasets": datasets}

@app.get("/llamadas/resumen-por-dia")
async def resumen_por_dia(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    grupo: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(
            func.date(Llamada.fecha).label("dia"),
            func.count().label("total"),
            func.sum(Llamada.duracion_seg).label("duracion_total")
        )
        .group_by(func.date(Llamada.fecha))
        .order_by(func.date(Llamada.fecha))
    )

    if fecha_inicio:
        query = query.where(Llamada.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.where(Llamada.fecha <= fecha_fin)
    if grupo:
        query = query.where(Llamada.grupo_timbrado == grupo)

    result = await db.execute(query)
    resumen = result.all()

    return [
        {
            "dia": row.dia.isoformat(),
            "total_llamadas": row.total,
            "duracion_total": row.duracion_total
        }
        for row in resumen
    ]

@app.get("/llamadas/resumen-mensual")
async def resumen_mensual(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            func.to_char(Llamada.fecha, 'YYYY-MM').label("mes"),
            func.count().label("total_llamadas")
        )
        .group_by("mes")
        .order_by("mes")
    )
    result = await db.execute(query)
    return [{"mes": row.mes, "total": row.total_llamadas} for row in result]

@app.get("/llamadas/por-agente")
async def llamadas_por_agente(
    estado: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    query = select(
        Llamada.extension,
        func.count().label("total")
    ).where(Llamada.extension.isnot(None)).where(Llamada.extension != "") \
     .group_by(Llamada.extension)

    if estado:
        if estado == "contestada":
            query = query.where(Llamada.estado == "ANSWERED")
        elif estado == "no_contestada":
            query = query.where(Llamada.estado == "NO ANSWER")
        else:
            query = query.where(Llamada.estado == estado)

    result = await db.execute(query)
    return [{"extension": row[0], "total": row[1]} for row in result]

@app.get("/llamadas/duracion-por-agente")
async def duracion_promedio_agente(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            Llamada.extension,
            func.avg(Llamada.duracion_seg).label("promedio")
        )
        .where(Llamada.extension.isnot(None))
        .where(Llamada.extension != "")
        .group_by(Llamada.extension)
    )
    result = await db.execute(query)
    return [{"extension": row[0], "promedio": row[1]} for row in result]