from sqlalchemy import Column, Integer, String, Float, Boolean, \
    DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    precio_cents = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    categoria = Column(String(50))
    tallas = Column(String(100))
    activo = Column(Boolean, default=True)

    def precio_euros(self):
        return self.precio_cents / 100

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False)
    nombre_cliente = Column(String(100))
    email_cliente = Column(String(100))
    direccion = Column(String(200))
    estado = Column(String(50), default="pendiente")
    total_cents = Column(Integer, default=0)
    notas = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    lineas = relationship("LineaPedido", back_populates="pedido")

class LineaPedido(Base):
    __tablename__ = "lineas_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, default=1)
    precio_unidad_cents = Column(Integer)
    talla = Column(String(10))

    pedido = relationship("Pedido", back_populates="lineas")

class SolicitudFactura(Base):
    __tablename__ = "solicitudes_factura"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100))
    email_cliente = Column(String(100))
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    procesada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)

class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    mensaje = Column(Text)
    enviada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    clave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text, nullable=False)
    descripcion = Column(String(200))
