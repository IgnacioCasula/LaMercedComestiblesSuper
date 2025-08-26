# nombredeapp/models.py
# CÓDIGO COMPLETO, CORREGIDO Y ESTANDARIZADO A ESPAÑOL

from django.db import models
import uuid

# --- MODELOS PRINCIPALES ---

class Rol(models.Model):
    idroles = models.AutoField(db_column='IdRoles', primary_key=True)
    nombrerol = models.CharField(db_column='NombreRol', max_length=50, verbose_name="Nombre del Rol")
    descripcionrol = models.CharField(db_column='DescripcionRol', max_length=200, blank=True, null=True, verbose_name="Descripción del Rol")

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        db_table = 'roles'

    def __str__(self):
        return self.nombrerol

class Usuario(models.Model):
    idusuarios = models.AutoField(db_column='IdUsuarios', primary_key=True)
    nombreusuario = models.CharField(db_column='NombreUsuario', max_length=30, unique=True, verbose_name="Nombre de Usuario")
    apellidousuario = models.CharField(db_column='ApellidoUsuario', max_length=30, verbose_name="Apellido")
    emailusuario = models.CharField(db_column='EmailUsuario', max_length=50, unique=True, verbose_name="Email")
    passwordusuario = models.CharField(db_column='PasswordUsuario', max_length=255, verbose_name="Contraseña")
    fecharegistrousuario = models.DateField(db_column='FechaRegistroUsuario', verbose_name="Fecha de Registro")
    dniusuario = models.BigIntegerField(db_column='DNIUsuario', unique=True, verbose_name="DNI")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    roles = models.ManyToManyField(Rol, through='UsuarioRol')

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombreusuario} {self.apellidousuario}'

class Empleado(models.Model):
    class Estado(models.TextChoices):
        TRABAJANDO = 'Trabajando', 'Trabajando'
        DESPEDIDO = 'Despedido', 'Despedido'
        RENUNCIO = 'Renuncio', 'Renunció'

    idempleado = models.AutoField(db_column='IdEmpleado', primary_key=True)
    usuario = models.OneToOneField(Usuario, models.CASCADE, db_column='IdUsuarios')
    salarioempleado = models.FloatField(db_column='SalarioEmpleado', verbose_name="Salario")
    fechacontratado = models.DateField(db_column='FechaContratado', verbose_name="Fecha de Contratación")
    cargoempleado = models.CharField(db_column='CargoEmpleado', max_length=100, verbose_name="Cargo")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.TRABAJANDO)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        db_table = 'empleados'

    def __str__(self):
        return f'{self.usuario.nombreusuario} {self.usuario.apellidousuario}'

# --- MODELOS RELACIONADOS CON LA UBICACIÓN ---

class CodigoPostal(models.Model):
    idcodigopostal = models.AutoField(db_column='IdCodigoPostal', primary_key=True)
    codigopostal = models.BigIntegerField(db_column='CodigoPostal')
    nombrelocalidad = models.CharField(db_column='NombreLocalidad', max_length=30)

    class Meta:
        db_table = 'codigopostal'

    def __str__(self):
        return f'{self.codigopostal} - {self.nombrelocalidad}'

class Ubicacion(models.Model):
    idubicacion = models.AutoField(db_column='IdUbicacion', primary_key=True)
    codigopostal = models.ForeignKey(CodigoPostal, models.DO_NOTHING, db_column='IdCodigoPostal')
    ciudad = models.CharField(db_column='Ciudad', max_length=50)
    nombrecalle = models.CharField(db_column='NombreCalle', max_length=50)
    barrio = models.CharField(db_column='Barrio', max_length=50)

    class Meta:
        db_table = 'ubicaciones'

    def __str__(self):
        return f'{self.nombrecalle}, {self.barrio}, {self.ciudad}'

class Sucursal(models.Model):
    idsucursal = models.AutoField(db_column='IdSucursal', primary_key=True)
    ubicacion = models.ForeignKey(Ubicacion, models.DO_NOTHING, db_column='IdUbicacion')
    nombresucursal = models.CharField(db_column='NombreSucursal', max_length=30)
    telefonosucursal = models.BigIntegerField(db_column='TelefonoSucursal')

    class Meta:
        db_table = 'sucursales'

    def __str__(self):
        return self.nombresucursal

# --- MODELOS RELACIONADOS CON PRODUCTOS Y STOCK ---

class Categoria(models.Model):
    idcategoria = models.AutoField(db_column='IdCategoria', primary_key=True)
    nombrecategoria = models.CharField(db_column='NombreCategoria', max_length=30)
    descripcioncategoria = models.CharField(db_column='DescripcionCategoria', max_length=50)

    class Meta:
        db_table = 'categorias'
    
    def __str__(self):
        return self.nombrecategoria

class Producto(models.Model):
    idproducto = models.AutoField(db_column='IdProducto', primary_key=True)
    categoria = models.ForeignKey(Categoria, models.DO_NOTHING, db_column='IdCategoria')
    nombreproductos = models.CharField(db_column='NombreProductos', max_length=50)
    precioproducto = models.FloatField(db_column='PrecioProducto')
    marcaproducto = models.CharField(db_column='MarcaProducto', max_length=50)
    codigobarraproducto = models.BigIntegerField(db_column='CodigoBarraProducto', unique=True)

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return f'{self.nombreproductos} ({self.marcaproducto})'

class Inventario(models.Model):
    idinventario = models.AutoField(db_column='IdInventario', primary_key=True)
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')
    stockactual = models.IntegerField(db_column='StockActual')
    stockminimo = models.IntegerField(db_column='StockMinimo')
    fechareposicion = models.DateField(db_column='FechaReposicion', blank=True, null=True)

    class Meta:
        db_table = 'inventarios'

# --- MODELOS DE PROVEEDORES Y COMPRAS ---

class Proveedor(models.Model):
    idproveedor = models.AutoField(db_column='IdProveedor', primary_key=True)
    nombreproveedor = models.CharField(db_column='NombreProveedor', max_length=30)
    telefonoproveedor = models.BigIntegerField(db_column='TelefonoProveedor')
    emailprov = models.CharField(db_column='EmailProv', max_length=30)
    cuitproveedor = models.BigIntegerField(db_column='CUITProveedor')

    class Meta:
        db_table = 'proveedores'

    def __str__(self):
        return self.nombreproveedor

class Caja(models.Model):
    idcaja = models.AutoField(db_column='IdCaja', primary_key=True)
    nombrecaja = models.CharField(db_column='NombreCaja', max_length=50)
    horaaperturacaja = models.TimeField(db_column='HoraAperturaCaja')
    horacierrecaja = models.TimeField(db_column='HoraCierreCaja')
    fechaaperturacaja = models.DateField(db_column='FechaAperturaCaja')
    fechacierrecaja = models.DateField(db_column='FechaCierreCaja')
    montoinicialcaja = models.FloatField(db_column='MontoInicialCaja')
    montofinalcaja = models.FloatField(db_column='MontoFinalCaja')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='IdUsuarios')

    class Meta:
        db_table = 'cajas'
    
    def __str__(self):
        return self.nombrecaja

class Compra(models.Model):
    idcompras = models.AutoField(db_column='IdCompras', primary_key=True)
    proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='IdProveedor')
    caja = models.ForeignKey(Caja, models.DO_NOTHING, db_column='IdCaja')
    fechacompra = models.DateField(db_column='FechaCompra')
    horacompra = models.TimeField(db_column='HoraCompra')
    totalcompra = models.FloatField(db_column='TotalCompra')
    estadocompra = models.CharField(db_column='EstadoCompra', max_length=50)

    class Meta:
        db_table = 'compras'

    def __str__(self):
        return f'Compra #{self.idcompras} a {self.proveedor.nombreproveedor}'

class DetalleCompra(models.Model):
    iddetallecompras = models.AutoField(db_column='IdDetalleCompras', primary_key=True)
    compra = models.ForeignKey(Compra, models.DO_NOTHING, db_column='IdCompras')
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    cantidadcompra = models.IntegerField(db_column='CantidadCompra')
    preciounitariodc = models.FloatField(db_column='PrecioUnitarioDC')
    subtotaldc = models.FloatField(db_column='SubtotalDC')

    class Meta:
        db_table = 'detallecompras'

# --- MODELOS DE VENTAS Y PEDIDOS ---

class Oferta(models.Model):
    idofertas = models.AutoField(db_column='IdOfertas', primary_key=True)
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    nombreoferta = models.CharField(db_column='NombreOferta', max_length=30)
    descripcionoferta = models.CharField(db_column='DescripcionOferta', max_length=50)
    fechainiciooferta = models.DateField(db_column='FechaInicioOferta')
    fechafinoferta = models.DateField(db_column='FechaFinOferta')
    valordescuento = models.FloatField(db_column='ValorDescuento')

    class Meta:
        db_table = 'ofertas'

    def __str__(self):
        return self.nombreoferta

class Venta(models.Model):
    idventa = models.AutoField(db_column='IdVenta', primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='IdUsuarios')
    caja = models.ForeignKey(Caja, models.DO_NOTHING, db_column='IdCaja')
    oferta = models.ForeignKey(Oferta, models.DO_NOTHING, db_column='IdOfertas', blank=True, null=True)
    totalventa = models.FloatField(db_column='TotalVenta')
    metodopago = models.CharField(db_column='MetodoPago', max_length=50)
    estadoventa = models.CharField(db_column='EstadoVenta', max_length=50)
    fechaventa = models.DateField(db_column='FechaVenta')
    horaventa = models.TimeField(db_column='HoraVenta')

    class Meta:
        db_table = 'ventas'

    def __str__(self):
        return f'Venta #{self.idventa}'

class DetalleVenta(models.Model):
    iddetalleventas = models.AutoField(db_column='IdDetalleVentas', primary_key=True)
    venta = models.ForeignKey(Venta, models.DO_NOTHING, db_column='IdVenta')
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    cantidadvendida = models.IntegerField(db_column='CantidadVendida')
    preciounitariodv = models.FloatField(db_column='PrecioUnitarioDV')
    subtotaldv = models.FloatField(db_column='SubtotalDV')

    class Meta:
        db_table = 'detalleventas'

class Pedido(models.Model):
    idpedidos = models.AutoField(db_column='IdPedidos', primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='IdUsuarios')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')
    fechapedido = models.DateField(db_column='FechaPedido')
    fechamaxretiro = models.DateField(db_column='FechaMaxRetiro')
    estadopedido = models.CharField(db_column='EstadoPedido', max_length=30)
    codigoretiro = models.CharField(db_column='CodigoRetiro', max_length=50)

    class Meta:
        db_table = 'pedidos'

    def __str__(self):
        return f'Pedido #{self.idpedidos} de {self.usuario.nombreusuario}'

class DetallePedido(models.Model):
    iddetallepedido = models.AutoField(db_column='IdDetallePedido', primary_key=True)
    pedido = models.ForeignKey(Pedido, models.DO_NOTHING, db_column='IdPedidos')
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    cantidadpedido = models.IntegerField(db_column='CantidadPedido')
    preciounitariopedido = models.FloatField(db_column='PrecioUnitarioPedido')

    class Meta:
        db_table = 'detallepedido'

# --- TABLAS DE UNIÓN Y REGISTROS ---

class Asistencia(models.Model):
    idasistencia = models.AutoField(db_column='IdAsistencia', primary_key=True)
    empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='IdEmpleado')
    fechaasistencia = models.DateField(db_column='FechaAsistencia')
    horaentrada = models.TimeField(db_column='HoraEntrada')
    horasalida = models.TimeField(db_column='HoraSalida', blank=True, null=True)

    class Meta:
        db_table = 'asistencias'

class EmpleadoPorSucursal(models.Model):
    idempleadosucursales = models.AutoField(db_column='IdEmpleadoSucursales', primary_key=True)
    empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='IdEmpleado')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')
    fechaaltaempleado = models.DateField(db_column='FechaAltaEmpleado')
    fechabajaempleado = models.DateField(db_column='FechaBajaEmpleado', blank=True, null=True)

    class Meta:
        db_table = 'empleadosxsucursales'

class ProveedorPorProducto(models.Model):
    idproveedorxproducto = models.AutoField(db_column='IdProveedorxProducto', primary_key=True)
    proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='IdProveedor')
    producto = models.ForeignKey(Producto, models.DO_NOTHING, db_column='IdProducto')
    descripcionpxp = models.CharField(db_column='DescripcionPxP', max_length=50)

    class Meta:
        db_table = 'proveedorxproductos'

class ProveedorPorSucursal(models.Model):
    idproveedorsucursal = models.AutoField(db_column='IdProveedorSucursal', primary_key=True)
    proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='IdProveedor')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')
    fechavisita = models.DateField(db_column='FechaVisita')

    class Meta:
        db_table = 'proveedorxsucursales'

class UsuarioRol(models.Model):
    idusuariorol = models.AutoField(db_column='IdUsuarioRol', primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='IdUsuarios')
    rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='IdRoles')

    class Meta:
        db_table = 'usuariosxrol'
        unique_together = (('usuario', 'rol'),)

class UsuarioPorSucursal(models.Model):
    idusuariosucursales = models.AutoField(db_column='IdUsuarioSucursales', primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, db_column='IdUsuarios')
    sucursal = models.ForeignKey(Sucursal, models.DO_NOTHING, db_column='IdSucursal')

    class Meta:
        db_table = 'usuarioxsucursales'

# --- MODELOS DE SEGURIDAD Y AUTENTICACIÓN ---

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
