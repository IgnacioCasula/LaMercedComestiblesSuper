# (Importaciones y otros modelos se mantienen igual)
from django.db import models
import uuid

# ... (Area, Roles, Usuarios, Empleados, etc. se mantienen igual) ...

class Area(models.Model):
    idarea = models.AutoField(primary_key=True)
    nombrearea = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'areas'
        verbose_name = "Área"
        verbose_name_plural = "Áreas"

    def __str__(self):
        return self.nombrearea

class Roles(models.Model):
    idroles = models.AutoField(db_column='IdRoles', primary_key=True)
    nombrerol = models.CharField(db_column='NombreRol', max_length=50)
    descripcionrol = models.CharField(db_column='DescripcionRol', max_length=200, blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        if self.area:
            return f"{self.area.nombrearea} - {self.nombrerol}"
        return self.nombrerol or ''

class Usuarios(models.Model):
    idusuarios = models.AutoField(db_column='IdUsuarios', primary_key=True)
    nombreusuario = models.CharField(db_column='NombreUsuario', max_length=30, unique=True)
    apellidousuario = models.CharField(db_column='ApellidoUsuario', max_length=30)
    emailusuario = models.CharField(db_column='EmailUsuario', max_length=50, unique=True)
    passwordusuario = models.CharField(db_column='PasswordUsuario', max_length=255)
    fecharegistrousuario = models.DateField(db_column='FechaRegistroUsuario')
    dniusuario = models.BigIntegerField(db_column='DNIUsuario', unique=True)
    imagenusuario = models.TextField(db_column='ImagenUsuario', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    roles = models.ManyToManyField(Roles, through='Usuariosxrol')

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombreusuario} {self.apellidousuario}'

class Empleados(models.Model):
    idempleado = models.AutoField(db_column='IdEmpleado', primary_key=True)
    salarioempleado = models.FloatField(db_column='SalarioEmpleado')
    fechacontratado = models.DateField(db_column='FechaContratado')
    cargoempleado = models.CharField(db_column='CargoEmpleado', max_length=100)
    idusuarios = models.OneToOneField(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    estado = models.CharField(max_length=20, default='Trabajando')

    class Meta:
        db_table = 'empleados'

# ... (Codigopostal, Ubicaciones, Sucursales, Proveedores, Cajas, Categorias, etc. se mantienen igual) ...

class Codigopostal(models.Model):
    idcodigopostal = models.AutoField(db_column='IdCodigoPostal', primary_key=True)
    codigopostal = models.BigIntegerField(db_column='CodigoPostal')
    nombrelocalidad = models.CharField(db_column='NombreLocalidad', max_length=30)

    class Meta:
        db_table = 'codigopostal'

class Ubicaciones(models.Model):
    idubicacion = models.AutoField(db_column='IdUbicacion', primary_key=True)
    ciudad = models.CharField(db_column='Ciudad', max_length=50)
    nombrecalle = models.CharField(db_column='NombreCalle', max_length=50)
    barrio = models.CharField(db_column='Barrio', max_length=50)
    idcodigopostal = models.ForeignKey(Codigopostal, on_delete=models.CASCADE, db_column='IdCodigoPostal')

    class Meta:
        db_table = 'ubicaciones'

class Sucursales(models.Model):
    idsucursal = models.AutoField(db_column='IdSucursal', primary_key=True)
    nombresucursal = models.CharField(db_column='NombreSucursal', max_length=30)
    telefonosucursal = models.BigIntegerField(db_column='TelefonoSucursal')
    idubicacion = models.ForeignKey(Ubicaciones, on_delete=models.CASCADE, db_column='IdUbicacion')

    class Meta:
        db_table = 'sucursales'

class Proveedores(models.Model):
    idproveedor = models.AutoField(db_column='IdProveedor', primary_key=True)
    nombreproveedor = models.CharField(db_column='NombreProveedor', max_length=30)
    telefonoproveedor = models.BigIntegerField(db_column='TelefonoProveedor')
    emailprov = models.CharField(db_column='EmailProv', max_length=30)
    cuitproveedor = models.BigIntegerField(db_column='CUITProveedor', unique=True)

    class Meta:
        db_table = 'proveedores'

class Cajas(models.Model):
    idcaja = models.AutoField(db_column='IdCaja', primary_key=True)
    nombrecaja = models.CharField(db_column='NombreCaja', max_length=50)
    horaaperturacaja = models.TimeField(db_column='HoraAperturaCaja')
    horacierrecaja = models.TimeField(db_column='HoraCierreCaja')
    fechaaperturacaja = models.DateField(db_column='FechaAperturaCaja')
    fechacierrecaja = models.DateField(db_column='FechaCierreCaja')
    montoinicialcaja = models.FloatField(db_column='MontoInicialCaja')
    montofinalcaja = models.FloatField(db_column='MontoFinalCaja')
    observacionapertura = models.CharField(db_column='Observacionapertura', max_length=100, blank=True, null=True)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')

    class Meta:
        db_table = 'cajas'

class Categorias(models.Model):
    idcategoria = models.AutoField(db_column='IdCategoria', primary_key=True)
    nombrecategoria = models.CharField(db_column='NombreCategoria', max_length=30)
    descripcioncategoria = models.CharField(db_column='DescripcionCategoria', max_length=50)

    class Meta:
        db_table = 'categorias'

class Productos(models.Model):
    idproducto = models.AutoField(db_column='IdProducto', primary_key=True)
    nombreproductos = models.CharField(db_column='NombreProductos', max_length=50)
    precioproducto = models.FloatField(db_column='PrecioProducto')
    marcaproducto = models.CharField(db_column='MarcaProducto', max_length=50)
    codigobarraproducto = models.BigIntegerField(db_column='CodigoBarraProducto', unique=True)
    imagenproducto = models.TextField(db_column='ImagenProducto', blank=True, null=True)
    idcategoria = models.ForeignKey(Categorias, on_delete=models.CASCADE, db_column='IdCategoria')

    class Meta:
        db_table = 'productos'

class Compras(models.Model):
    idcompras = models.AutoField(db_column='IdCompras', primary_key=True)
    fechacompra = models.DateField(db_column='FechaCompra')
    horacompra = models.TimeField(db_column='HoraCompra')
    totalcompra = models.FloatField(db_column='TotalCompra')
    estadocompra = models.CharField(db_column='EstadoCompra', max_length=50)
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE, db_column='IdProveedor')
    idcaja = models.ForeignKey(Cajas, on_delete=models.CASCADE, db_column='IdCaja')

    class Meta:
        db_table = 'compras'

class Detallecompras(models.Model):
    iddetallecompras = models.AutoField(db_column='IdDetalleCompras', primary_key=True)
    cantidadcompra = models.IntegerField(db_column='CantidadCompra')
    preciounitariodc = models.FloatField(db_column='PrecioUnitarioDC')
    subtotaldc = models.FloatField(db_column='SubtotalDC')
    idcompras = models.ForeignKey(Compras, on_delete=models.CASCADE, db_column='IdCompras')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'detallecompras'

class Ventas(models.Model):
    idventa = models.AutoField(db_column='IdVenta', primary_key=True)
    totalventa = models.FloatField(db_column='TotalVenta')
    metodopago = models.CharField(db_column='MetodoPago', max_length=50)
    estadoventa = models.CharField(db_column='EstadoVenta', max_length=50)
    fechaventa = models.DateField(db_column='FechaVenta')
    horaventa = models.TimeField(db_column='HoraVenta')
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idofertas = models.ForeignKey('Ofertas', on_delete=models.CASCADE, db_column='IdOfertas')
    idcaja = models.ForeignKey(Cajas, on_delete=models.CASCADE, db_column='IdCaja')

    class Meta:
        db_table = 'ventas'

class Detalleventas(models.Model):
    iddetalleventas = models.AutoField(db_column='IdDetalleVentas', primary_key=True)
    cantidadvendida = models.IntegerField(db_column='CantidadVendida')
    preciounitariodv = models.FloatField(db_column='PrecioUnitarioDV')
    subtotaldv = models.FloatField(db_column='SubtotalDV')
    idventa = models.ForeignKey(Ventas, on_delete=models.CASCADE, db_column='IdVenta')
    idprducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdPrducto')

    class Meta:
        db_table = 'detalleventas'

class Ofertas(models.Model):
    idofertas = models.AutoField(db_column='IdOfertas', primary_key=True)
    nombreoferta = models.CharField(db_column='NombreOferta', max_length=30)
    descripcionoferta = models.CharField(db_column='DescripcionOferta', max_length=50)
    fechainiciooferta = models.DateField(db_column='FechaInicioOferta')
    fechafinoferta = models.DateField(db_column='FechaFinOferta')
    valordescuento = models.FloatField(db_column='ValorDescuento')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'ofertas'

class Pedidos(models.Model):
    idpedidos = models.AutoField(db_column='IdPedidos', primary_key=True)
    fechapedido = models.DateField(db_column='FechaPedido')
    fechamaxretiro = models.DateField(db_column='FechaMaxRetiro')
    estadopedido = models.CharField(db_column='EstadoPedido', max_length=30)
    codigoretiro = models.CharField(db_column='CodigoRetiro', max_length=50)
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')

    class Meta:
        db_table = 'pedidos'

class Detallepedido(models.Model):
    iddetallepedido = models.AutoField(db_column='IdDetallePedido', primary_key=True)
    cantidadpedido = models.IntegerField(db_column='CantidadPedido')
    preciounitariopedido = models.FloatField(db_column='PrecioUnitarioPedido')
    idpedidos = models.ForeignKey(Pedidos, on_delete=models.CASCADE, db_column='IdPedidos')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'detallepedido'

class Usuariosxrol(models.Model):
    idusuarioxrol = models.AutoField(primary_key=True)
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idroles = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='IdRoles')

    class Meta:
        db_table = 'usuariosxrol'
        unique_together = [['idusuarios', 'idroles']]

class Asistencias(models.Model):
    idasistencia = models.AutoField(db_column='IdAsistencia', primary_key=True)
    fechaasistencia = models.DateField(db_column='FechaAsistencia')
    horaentrada = models.TimeField(db_column='HoraEntrada')
    horasalida = models.TimeField(db_column='HoraSalida', null=True, blank=True)
    idempleado = models.ForeignKey(Empleados, on_delete=models.CASCADE, db_column='IdEmpleado')
    # --- CAMPO NUEVO ---
    rol = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True, help_text="Rol con el que se registró esta asistencia")

    class Meta:
        db_table = 'asistencias'

class Empleadosxsucursales(models.Model):
    idempleadosucursales = models.AutoField(db_column='IdEmpleadoSucursales', primary_key=True)
    fechaaltaempleado = models.DateField(db_column='FechaAltaEmpleado')
    fechabajaempleado = models.DateField(db_column='FechaBajaEmpleado', blank=True, null=True)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')
    idempleado = models.ForeignKey(Empleados, on_delete=models.CASCADE, db_column='IdEmpleado')

    class Meta:
        db_table = 'empleadosxsucursales'

class Proveedorxproductos(models.Model):
    idproveedorxproducto = models.AutoField(db_column='IdProveedorxProducto', primary_key=True)
    descripcionpxp = models.CharField(db_column='DescripcionPxP', max_length=50)
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE, db_column='IdProveedor')

    class Meta:
        db_table = 'proveedorxproductos'

class Proveedorxsucursales(models.Model):
    idproveedorsucursal = models.AutoField(db_column='IdProveedorSucursal', primary_key=True)
    fechavisita = models.DateField(db_column='FechaVisita')
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE, db_column='IdProveedor')
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')

    class Meta:
        db_table = 'proveedorxsucursales'

class Usuarioxsucursales(models.Model):
    idusuariosucursales = models.AutoField(db_column='IdUsuarioSucursales', primary_key=True)
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')

    class Meta:
        db_table = 'usuarioxsucursales'

class RegistroSeguridad(models.Model):
    id = models.AutoField(primary_key=True)
    direccion_ip = models.CharField(max_length=50)
    intento_usuario = models.CharField(max_length=100)
    intento_contrasena = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255)

class TokenRecuperacion(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    codigo_sms = models.CharField(max_length=5, blank=True, null=True)
    expiracion_codigo_sms = models.DateTimeField(blank=True, null=True)
    token_email = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiracion_token_email = models.DateTimeField()
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

class Herramienta(models.Model):
    idherramienta = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Herramienta")
    url_nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de URL (para {% url %})")
    icono = models.CharField(max_length=50, blank=True, null=True, verbose_name="Clase del Icono (ej: fa-users)")

    class Meta:
        db_table = 'herramientas'
        verbose_name = "Herramienta"
        verbose_name_plural = "Herramientas"

    def __str__(self):
        return self.nombre

class Permiso(models.Model):
    idpermiso = models.AutoField(primary_key=True)
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="permisos")
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE)

    class Meta:
        db_table = 'permisos'
        unique_together = [['rol', 'herramienta']]
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"

    def __str__(self):
        return f"El rol '{self.rol.nombrerol}' tiene permiso para '{self.herramienta.nombre}'"