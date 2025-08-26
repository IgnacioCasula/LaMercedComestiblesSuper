# nombredeapp/models.py (Versión final y corregida)

from django.db import models
import uuid

# --- IMPORTAMOS LOS MODELOS ORIGINALES DE LA APP 'caja' ---
from caja.models import (
    Roles,
    Usuarios,
    Empleados,
    Codigopostal as CodigoPostalOriginal,
    Ubicaciones as UbicacionOriginal,
    Sucursales as SucursalOriginal,
    Categorias as CategoriaOriginal,
    Productos as ProductoOriginal,
    Inventarios as InventarioOriginal,
    Proveedores,
    Cajas,
    Compras,
    Detallecompras as DetalleCompraOriginal,
    Ofertas,
    Ventas,
    Detalleventas as DetalleVentaOriginal,
    Pedidos,
    Detallepedido as DetallePedidoOriginal,
    Asistencias as AsistenciaOriginal,
    Empleadosxsucursales as EmpleadoPorSucursalOriginal,
    Proveedorxproductos as ProveedorPorProductoOriginal,
    Proveedorxsucursales as ProveedorPorSucursalOriginal,
    Usuariosxrol as UsuarioRolOriginal,
    Usuarioxsucursales as UsuarioPorSucursalOriginal
)

# --- MODELOS PROXY ---

class Rol(Roles):
    class Meta:
        proxy = True
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombrerol

class Usuario(Usuarios):
    class Meta:
        proxy = True
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f'{self.nombreusuario} {self.apellidousuario}'

class Empleado(Empleados):
    class Estado(models.TextChoices):
        TRABAJANDO = 'Trabajando', 'Trabajando'
        DESPEDIDO = 'Despedido', 'Despedido'
        RENUNCIO = 'Renuncio', 'Renunció'
        
    class Meta:
        proxy = True
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
    
    def __str__(self):
        # Usamos 'self.idusuarios' porque así se llama el campo en el modelo original de 'caja'
        return f'{self.idusuarios.nombreusuario} {self.idusuarios.apellidousuario}'

class CodigoPostal(CodigoPostalOriginal):
    class Meta:
        proxy = True
    def __str__(self):
        return f'{self.codigopostal} - {self.nombrelocalidad}'

class Ubicacion(UbicacionOriginal):
    class Meta:
        proxy = True
    def __str__(self):
        return f'{self.nombrecalle}, {self.barrio}, {self.ciudad}'

class Sucursal(SucursalOriginal):
    class Meta:
        proxy = True
    def __str__(self):
        return self.nombresucursal

class Categoria(CategoriaOriginal):
    class Meta:
        proxy = True
    def __str__(self):
        return self.nombrecategoria

class Producto(ProductoOriginal):
    class Meta:
        proxy = True
    def __str__(self):
        return f'{self.nombreproductos} ({self.marcaproducto})'

class Inventario(InventarioOriginal):
    class Meta:
        proxy = True

class Proveedor(Proveedores):
    class Meta:
        proxy = True
    def __str__(self):
        return self.nombreproveedor

class Caja(Cajas):
    class Meta:
        proxy = True
    def __str__(self):
        return self.nombrecaja

class Compra(Compras):
    class Meta:
        proxy = True
    def __str__(self):
        # Usamos 'self.idproveedor' porque así se llama el campo en el modelo original
        return f'Compra #{self.idcompras} a {self.idproveedor.nombreproveedor}'

class DetalleCompra(DetalleCompraOriginal):
    class Meta:
        proxy = True

class Oferta(Ofertas):
    class Meta:
        proxy = True
    def __str__(self):
        return self.nombreoferta

class Venta(Ventas):
    class Meta:
        proxy = True
    def __str__(self):
        return f'Venta #{self.idventa}'

class DetalleVenta(DetalleVentaOriginal):
    class Meta:
        proxy = True

class Pedido(Pedidos):
    class Meta:
        proxy = True
    def __str__(self):
        # Usamos 'self.idusuarios' porque así se llama el campo en el modelo original
        return f'Pedido #{self.idpedidos} de {self.idusuarios.nombreusuario}'

class DetallePedido(DetallePedidoOriginal):
    class Meta:
        proxy = True

class Asistencia(AsistenciaOriginal):
    class Meta:
        proxy = True

class EmpleadoPorSucursal(EmpleadoPorSucursalOriginal):
    class Meta:
        proxy = True

class ProveedorPorProducto(ProveedorPorProductoOriginal):
    class Meta:
        proxy = True

class ProveedorPorSucursal(ProveedorPorSucursalOriginal):
    class Meta:
        proxy = True

class UsuarioRol(UsuarioRolOriginal):
    class Meta:
        proxy = True

class UsuarioPorSucursal(UsuarioPorSucursalOriginal):
    class Meta:
        proxy = True

# --- MODELOS QUE SOLO EXISTEN EN 'nombredeapp' ---

class RegistroSeguridad(models.Model):
    id = models.AutoField(primary_key=True)
    direccion_ip = models.CharField(max_length=50)
    intento_usuario = models.CharField(max_length=100)
    intento_contrasena = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Registro de Seguridad"
        verbose_name_plural = "Registros de Seguridad"

class TokenRecuperacion(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    codigo_sms = models.CharField(max_length=5, blank=True, null=True)
    expiracion_codigo_sms = models.DateTimeField(blank=True, null=True)
    token_email = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiracion_token_email = models.DateTimeField()
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Token de Recuperación"
        verbose_name_plural = "Tokens de Recuperación"