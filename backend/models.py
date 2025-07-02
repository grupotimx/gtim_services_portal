from sqlalchemy import Column, String, Integer, DateTime
from database import Base

class Llamada(Base):
    __tablename__ = "gtim_pbx_adaptix_calls"

    record_id = Column(String(36), primary_key=True, index=True)
    process_id = Column(String(36))
    fecha = Column(DateTime(timezone=True))
    caller_id = Column(String(15))
    grupo_timbrado = Column(String(30))
    destino = Column(String(30))
    canal_origen = Column(String(30))
    codigo_cuenta = Column(String(30))
    canal_destino = Column(String(30))
    estado = Column(String(30))
    duracion = Column(String(30))         # Ojo: este campo parece texto, por ejemplo "00:02:14"
    duracion_seg = Column(Integer)        # Este es numérico
    extension = Column(String(15))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
