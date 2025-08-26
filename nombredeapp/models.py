# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
import uuid

# Se han eliminado los modelos duplicados de auth_* y django_* para resolver el conflicto.

class Roles(models.Model):
    idroles = models.AutoField(db_column='IdRoles', primary_key=True)
    nombrerol = models.CharField(db_column='NombreRol', max_length=50)
    descripcionrol = models.CharField(db_column='DescripcionRol', max_length=200, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'roles'

    def __str__(self):
        return self.nombrerol

class Usuarios(models.Model):
    idusuarios = models.AutoField(db_column='IdUsuarios', primary_key=True)
    nombreusuario = models.CharField(db_column='NombreUsuario', max_length=30, unique=True)
    apellidousuario = models.CharField(db_column='ApellidoUsuario', max_length=30)
    emailusuario = models.CharField(db_column='EmailUsuario', max_length=50, unique=True)
    passwordusuario = models.CharField(db_column='PasswordUsuario', max_length=255)
    fecharegistrousuario = models.DateField(db_column='FechaRegistroUsuario')
    dniusuario = models.BigIntegerField(db_column='DNIUsuario', unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True) 
    roles = models.ManyToManyField(Roles, through='Usuariosxrol')

    class Meta:
        managed = True
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombreusuario} {self.apellidousuario}'

class Empleados(models.Model):
    ESTADO_CHOICES = [
        ('Trabajando', 'Trabajando'),
        ('Despedido', 'Despedido'),
        ('Renuncio', 'Renunció'),
    ]
    idempleado = models.AutoField(db_column='IdEmpleado', primary_key=True)
    usuario = models.OneToOneField(Usuarios, models.CASCADE, db_column='IdUsuarios')
    salarioempleado = models.FloatField(db_column='SalarioEmpleado')
    fechacontratado = models.DateField(db_column='FechaContratado')
    cargoempleado = models.CharField(db_column='CargoEmpleado', max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Trabajando')

    class Meta:
        managed = True
        db_table = 'empleados'

    def __str__(self):
        return f'{self.usuario.nombreusuario} {self.usuario.apellidousuario}'

class Asistencias(models.Model):
    idasistencia = models.AutoField(db_column='IdAsistencia', primary_key=True)
    empleado = models.ForeignKey(Empleados, models.DO_NOTHING, db_column='IdEmpleado')
    fechaasistencia = models.DateField(db_column='FechaAsistencia')
    horaentrada = models.TimeField(db_column='HoraEntrada')
    horasalida = models.TimeField(db_column='HoraSalida', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'asistencias'

class Cajas(models.Model):
    idcaja = models.AutoField(db_column='IdCaja', primary_key=True)
    nombrecaja = models.CharField(db_column='NombreCaja', max_length=50)
    horaaperturacaja = models.TimeField(db_column='HoraAperturaCaja')
    horacierrecaja = models.TimeField(db_column='HoraCierreCaja')
    fechaaperturacaja = models.DateField(db_column='FechaAperturaCaja')
    fechacierrecaja = models.DateField(db_column='FechaCierreCaja')
    montoinicialcaja = models.FloatField(db_column='MontoInicialCaja')
    montofinalcaja = models.FloatField(db_column='MontoFinalCaja')
    sucursal = models.ForeignKey('Sucursales', models.DO_NOTHING, db_column='IdSucursal')
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='IdUsuarios')

    class Meta:
        managed = True
        db_table = 'cajas'
    
    def __str__(self):
        return self.nombrecaja

class Categorias(models.Model):
    idcategoria = models.AutoField(db_column='IdCategoria', primary_key=True)
    nombrecategoria = models.CharField(db_column='NombreCategoria', max_length=30)
    descripcioncategoria = models.CharField(db_column='DescripcionCategoria', max_length=50)

    class Meta:
        managed = True
        db_table = 'categorias'
    
    def __str__(self):
        return self.nombrecategoria

class Codigopostal(models.Model):
    idcodigopostal = models.AutoField(db_column='IdCodigoPostal', primary_key=True)
    codigopostal = models.BigIntegerField(db_column='CodigoPostal')
    nombrelocalidad = models.CharField(db_column='NombreLocalidad', max_length=30)

    class Meta:
        managed = True
        db_table = 'codigopostal'

    def __str__(self):
        return f'{self.codigopostal} - {self.nombrelocalidad}'

class Proveedores(models.Model):
    idproveedor = models.AutoField(db_column='IdProveedor', primary_key=True)
    nombreproveedor = models.CharField(db_column='NombreProveedor', max_length=30)
    telefonoproveedor = models.BigIntegerField(db_column='TelefonoProveedor')
    emailprov = models.CharField(db_column='EmailProv', max_length=30)
    cuitproveedor = models.BigIntegerField(db_column='CUITProveedor')

    class Meta:
        managed = True
        db_table = 'proveedores'

    def __str__(self):
        return self.nombreproveedor

class Compras(models.Model):
    idcompras = models.AutoField(db_column='IdCompras', primary_key=True)
    proveedor = models.ForeignKey(Proveedores, models.DO_NOTHING, db_column='IdProveedor')
    caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='IdCaja')
    fechacompra = models.DateField(db_column='FechaCompra')
    horacompra = models.TimeField(db_column='HoraCompra')
    totalcompra = models.FloatField(db_column='TotalCompra')
    estadocompra = models.CharField(db_column='EstadoCompra', max_length=50)

    class Meta:
        managed = True
        db_table = 'compras'

    def __str__(self):
        return f'Compra #{self.idcompras} a {self.proveedor.nombreproveedor}'

class Productos(models.Model):
    idproducto = models.AutoField(db_column='IdProducto', primary_key=True)
    categoria = models.ForeignKey(Categorias, models.DO_NOTHING, db_column='IdCategoria')
    nombreproductos = models.CharField(db_column='NombreProductos', max_length=50)
    precioproducto = models.FloatField(db_column='PrecioProducto')
    marcaproducto = models.CharField(db_column='MarcaProducto', max_length=50)
    codigobarraproducto = models.BigIntegerField(db_column='CodigoBarraProducto', unique=True)

    class Meta:
        managed = True
        db_table = 'productos'

    def __str__(self):
        return f'{self.nombreproductos} ({self.marcaproducto})'

class Detallecompras(models.Model):
    iddetallecompras = models.AutoField(db_column='IdDetalleCompras', primary_key=True)
    compra = models.ForeignKey(Compras, models.DO_NOTHING, db_column='IdCompras')
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdProducto')
    cantidadcompra = models.IntegerField(db_column='CantidadCompra')
    preciounitariodc = models.FloatField(db_column='PrecioUnitarioDC')
    subtotaldc = models.FloatField(db_column='SubtotalDC')

    class Meta:
        managed = True
        db_table = 'detallecompras'

class Pedidos(models.Model):
    idpedidos = models.AutoField(db_column='IdPedidos', primary_key=True)
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='IdUsuarios')
    sucursal = models.ForeignKey('Sucursales', models.DO_NOTHING, db_column='IdSucursal')
    fechapedido = models.DateField(db_column='FechaPedido')
    fechamaxretiro = models.DateField(db_column='FechaMaxRetiro')
    estadopedido = models.CharField(db_column='EstadoPedido', max_length=30)
    codigoretiro = models.CharField(db_column='CodigoRetiro', max_length=50)

    class Meta:
        managed = True
        db_table = 'pedidos'

    def __str__(self):
        return f'Pedido #{self.idpedidos} de {self.usuario.nombreusuario}'

class Detallepedido(models.Model):
    iddetallepedido = models.AutoField(db_column='IdDetallePedido', primary_key=True)
    pedido = models.ForeignKey(Pedidos, models.DO_NOTHING, db_column='IdPedidos')
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdProducto')
    cantidadpedido = models.IntegerField(db_column='CantidadPedido')
    preciounitariopedido = models.FloatField(db_column='PrecioUnitarioPedido')

    class Meta:
        managed = True
        db_table = 'detallepedido'

class Ventas(models.Model):
    idventa = models.AutoField(db_column='IdVenta', primary_key=True)
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='IdUsuarios')
    caja = models.ForeignKey(Cajas, models.DO_NOTHING, db_column='IdCaja')
    oferta = models.ForeignKey('Ofertas', models.DO_NOTHING, db_column='IdOfertas', blank=True, null=True)
    totalventa = models.FloatField(db_column='TotalVenta')
    metodopago = models.CharField(db_column='MetodoPago', max_length=50)
    estadoventa = models.CharField(db_column='EstadoVenta', max_length=50)
    fechaventa = models.DateField(db_column='FechaVenta')
    horaventa = models.TimeField(db_column='HoraVenta')

    class Meta:
        managed = True
        db_table = 'ventas'

    def __str__(self):
        return f'Venta #{self.idventa}'

class Detalleventas(models.Model):
    iddetalleventas = models.AutoField(db_column='IdDetalleVentas', primary_key=True)
    venta = models.ForeignKey(Ventas, models.DO_NOTHING, db_column='IdVenta')
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdPrducto') # Ojo: nombre de columna original es IdPrducto
    cantidadvendida = models.IntegerField(db_column='CantidadVendida')
    preciounitariodv = models.FloatField(db_column='PrecioUnitarioDV')
    subtotaldv = models.FloatField(db_column='SubtotalDV')

    class Meta:
        managed = True
        db_table = 'detalleventas'

class Empleadosxsucursales(models.Model):
    idempleadosucursales = models.AutoField(db_column='IdEmpleadoSucursales', primary_key=True)
    empleado = models.ForeignKey(Empleados, models.DO_NOTHING, db_column='IdEmpleado')
    sucursal = models.ForeignKey('Sucursales', models.DO_NOTHING, db_column='IdSucursal')
    fechaaltaempleado = models.DateField(db_column='FechaAltaEmpleado')
    fechabajaempleado = models.DateField(db_column='FechaBajaEmpleado', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'empleadosxsucursales'

class Inventarios(models.Model):
    idinventario = models.AutoField(db_column='IdInventario', primary_key=True)
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdProducto')
    sucursal = models.ForeignKey('Sucursales', models.DO_NOTHING, db_column='IdSucursal')
    stockactual = models.IntegerField(db_column='StockActual')
    stockminimo = models.IntegerField(db_column='StockMinimo')
    fechareposicion = models.DateField(db_column='FechaReposicion', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'inventarios'

class Ofertas(models.Model):
    idofertas = models.AutoField(db_column='IdOfertas', primary_key=True)
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdProducto')
    nombreoferta = models.CharField(db_column='NombreOferta', max_length=30)
    descripcionoferta = models.CharField(db_column='DescripcionOferta', max_length=50)
    fechainiciooferta = models.DateField(db_column='FechaInicioOferta')
    fechafinoferta = models.DateField(db_column='FechaFinOferta')
    valordescuento = models.FloatField(db_column='ValorDescuento')

    class Meta:
        managed = True
        db_table = 'ofertas'

    def __str__(self):
        return self.nombreoferta

class Proveedorxproductos(models.Model):
    idproveedorxproducto = models.AutoField(db_column='IdProveedorxProducto', primary_key=True)
    proveedor = models.ForeignKey(Proveedores, models.DO_NOTHING, db_column='IdProveedor')
    producto = models.ForeignKey(Productos, models.DO_NOTHING, db_column='IdProducto')
    descripcionpxp = models.CharField(db_column='DescripcionPxP', max_length=50)

    class Meta:
        managed = True
        db_table = 'proveedorxproductos'

class Proveedorxsucursales(models.Model):
    idproveedorsucursal = models.AutoField(db_column='IdProveedorSucursal', primary_key=True)
    proveedor = models.ForeignKey(Proveedores, models.DO_NOTHING, db_column='IdProveedor')
    sucursal = models.ForeignKey('Sucursales', models.DO_NOTHING, db_column='IdSucursal')
    fechavisita = models.DateField(db_column='FechaVisita')

    class Meta:
        managed = True
        db_table = 'proveedorxsucursales'

class Ubicaciones(models.Model):
    idubicacion = models.AutoField(db_column='IdUbicacion', primary_key=True)
    codigopostal = models.ForeignKey(Codigopostal, models.DO_NOTHING, db_column='IdCodigoPostal')
    ciudad = models.CharField(db_column='Ciudad', max_length=50)
    nombrecalle = models.CharField(db_column='NombreCalle', max_length=50)
    barrio = models.CharField(db_column='Barrio', max_length=50)

    class Meta:
        managed = True
        db_table = 'ubicaciones'

    def __str__(self):
        return f'{self.nombrecalle}, {self.barrio}, {self.ciudad}'

class Sucursales(models.Model):
    idsucursal = models.AutoField(db_column='IdSucursal', primary_key=True)
    ubicacion = models.ForeignKey(Ubicaciones, models.DO_NOTHING, db_column='IdUbicacion')
    nombresucursal = models.CharField(db_column='NombreSucursal', max_length=30)
    telefonosucursal = models.BigIntegerField(db_column='TelefonoSucursal')

    class Meta:
        managed = True
        db_table = 'sucursales'

    def __str__(self):
        return self.nombresucursal

class Usuariosxrol(models.Model):
    idusuariorol = models.AutoField(db_column='IdUsuarioRol', primary_key=True)
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='IdUsuarios')
    rol = models.ForeignKey(Roles, models.DO_NOTHING, db_column='IdRoles')

    class Meta:
        managed = True
        db_table = 'usuariosxrol'
        unique_together = (('usuario', 'rol'),)

class Usuarioxsucursales(models.Model):
    idusuariosucursales = models.AutoField(db_column='IdUsuarioSucursales', primary_key=True)
    usuario = models.ForeignKey(Usuarios, models.DO_NOTHING, db_column='IdUsuarios')
    sucursal = models.ForeignKey(Sucursales, models.DO_NOTHING, db_column='IdSucursal')

    class Meta:
        managed = True
        db_table = 'usuarioxsucursales'

class SecurityLog(models.Model):
    id = models.AutoField(primary_key=True)
    ip_address = models.CharField(max_length=50)
    username_attempt = models.CharField(max_length=100)
    password_attempt = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255)

    def __str__(self):
        return f'Intento fallido de {self.username_attempt} en {self.timestamp}'

class PasswordResetToken(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    sms_code = models.CharField(max_length=5, blank=True, null=True)
    sms_code_expires_at = models.DateTimeField(blank=True, null=True)
    email_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email_token_expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token para {self.usuario.nombreusuario}"