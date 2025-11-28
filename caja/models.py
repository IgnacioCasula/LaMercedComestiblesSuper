from django.db import models
import uuid

class Codigopostal(models.Model):
    idcodigopostal = models.AutoField(db_column='IdCodigoPostal', primary_key=True)
    codigopostal = models.BigIntegerField(db_column='CodigoPostal')
    nombrelocalidad = models.CharField(db_column='NombreLocalidad', max_length=30)

    class Meta:
        db_table = 'codigosPostales'

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

class Inventarios(models.Model):
    idinventario = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventarios'
        unique_together = ('producto', 'sucursal')

class Provxprod(models.Model):
    idprovxprod = models.AutoField(primary_key=True)
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE)
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE)

    class Meta:
        db_table = 'provxprod'

class Provxsuc(models.Model):
    idprovxsuc = models.AutoField(primary_key=True)
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE)

    class Meta:
        db_table = 'provxsuc'

class Roles(models.Model):
    idroles = models.AutoField(db_column='IdRoles', primary_key=True)
    nombrerol = models.CharField(db_column='NombreRol', max_length=50)
    descripcionrol = models.CharField(db_column='DescripcionRol', max_length=200, blank=True, null=True)
    nombrearea = models.CharField(max_length=100, default="General")

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return f"{self.nombrearea} - {self.nombrerol}"

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
    roles = models.ManyToManyField(Roles, through='UsuxRoles')
    direccion = models.CharField(max_length=255, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    codigo_telefonico = models.CharField(max_length=10, default='+54')

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombreusuario} {self.apellidousuario}'

class UsuxRoles(models.Model):
    idusuarioxrol = models.AutoField(primary_key=True)
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idroles = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='IdRoles')

    class Meta:
        db_table = 'usuxRoles'
        unique_together = [['idusuarios', 'idroles']]

class Empleados(models.Model):
    idempleado = models.AutoField(db_column='IdEmpleado', primary_key=True)
    salarioempleado = models.FloatField(db_column='SalarioEmpleado')
    fechacontratado = models.DateField(db_column='FechaContratado')
    cargoempleado = models.CharField(db_column='CargoEmpleado', max_length=100)
    idusuarios = models.OneToOneField(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    estado = models.CharField(max_length=20, default='Trabajando')

    class Meta:
        db_table = 'empleados'

class EmpxSuc(models.Model):
    idempxsuc = models.AutoField(primary_key=True)
    idempleado = models.ForeignKey(Empleados, on_delete=models.CASCADE)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE)

    class Meta:
        db_table = 'empxSuc'

class UsuxSuc(models.Model):
    idusuxsuc = models.AutoField(primary_key=True)
    idusuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE)

    class Meta:
        db_table = 'usuxSuc'

class Caja(models.Model):
    idcaja = models.AutoField(db_column='IdCaja', primary_key=True)
    nombrecaja = models.CharField(db_column='NombreCaja', max_length=50)
    horaaperturacaja = models.TimeField(db_column='HoraAperturaCaja')
    horacierrecaja = models.TimeField(db_column='HoraCierreCaja')
    fechaaperturacaja = models.DateField(db_column='FechaAperturaCaja')
    fechacierrecaja = models.DateField(db_column='FechaCierreCaja')
    montoinicialcaja = models.FloatField(db_column='MontoInicialCaja')
    montofinalcaja = models.FloatField(db_column='MontoFinalCaja')
    # NUEVO CAMPO: Saldo actual en tiempo real
    saldo_actual = models.FloatField(db_column='SaldoActual', default=0.0)  # Todos los métodos de pago
    efectivo_actual = models.FloatField(db_column='EfectivoActual', default=0.0)  # Solo efectivo
    observacionapertura = models.CharField(db_column='Observacionapertura', max_length=100, blank=True, null=True)
    observacioncierre = models.CharField(db_column='Observacioncierre', max_length=100, blank=True, null=True)
    idsucursal = models.ForeignKey(Sucursales, on_delete=models.CASCADE, db_column='IdSucursal')
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')

    class Meta:
        db_table = 'caja'

class Compras(models.Model):
    idcompras = models.AutoField(db_column='IdCompras', primary_key=True)
    fechacompra = models.DateField(db_column='FechaCompra')
    horacompra = models.TimeField(db_column='HoraCompra')
    totalcompra = models.FloatField(db_column='TotalCompra')
    estadocompra = models.CharField(db_column='EstadoCompra', max_length=50)
    idproveedor = models.ForeignKey(Proveedores, on_delete=models.CASCADE, db_column='IdProveedor')
    idcaja = models.ForeignKey(Caja, on_delete=models.CASCADE, db_column='IdCaja')

    class Meta:
        db_table = 'compras'

class DetalleDeCompras(models.Model):
    iddetallecompras = models.AutoField(db_column='IdDetalleCompras', primary_key=True)
    cantidadcompra = models.IntegerField(db_column='CantidadCompra')
    preciounitariodc = models.FloatField(db_column='PrecioUnitarioDC')
    subtotaldc = models.FloatField(db_column='SubtotalDC')
    idcompras = models.ForeignKey(Compras, on_delete=models.CASCADE, db_column='IdCompras')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'detalleDeCompras'

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

class Ventas(models.Model):
    idventa = models.AutoField(db_column='IdVenta', primary_key=True)
    totalventa = models.FloatField(db_column='TotalVenta')
    metodopago = models.CharField(db_column='MetodoPago', max_length=50)
    estadoventa = models.CharField(db_column='EstadoVenta', max_length=50)
    fechaventa = models.DateField(db_column='FechaVenta')
    horaventa = models.TimeField(db_column='HoraVenta')
    idusuarios = models.ForeignKey(Usuarios, on_delete=models.CASCADE, db_column='IdUsuarios')
    idofertas = models.ForeignKey(Ofertas, on_delete=models.CASCADE, db_column='IdOfertas')
    idcaja = models.ForeignKey(Caja, on_delete=models.CASCADE, db_column='IdCaja')

    class Meta:
        db_table = 'ventas'

class DetalleDeVentas(models.Model):
    iddetalleventas = models.AutoField(db_column='IdDetalleVentas', primary_key=True)
    cantidadvendida = models.IntegerField(db_column='CantidadVendida')
    preciounitariodv = models.FloatField(db_column='PrecioUnitarioDV')
    subtotaldv = models.FloatField(db_column='SubtotalDV')
    idventa = models.ForeignKey(Ventas, on_delete=models.CASCADE, db_column='IdVenta')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'detalleDeVentas'

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

class DetalleDePedidos(models.Model):
    iddetallepedido = models.AutoField(db_column='IdDetallePedido', primary_key=True)
    cantidadpedido = models.IntegerField(db_column='CantidadPedido')
    preciounitariopedido = models.FloatField(db_column='PrecioUnitarioPedido')
    idpedidos = models.ForeignKey(Pedidos, on_delete=models.CASCADE, db_column='IdPedidos')
    idproducto = models.ForeignKey(Productos, on_delete=models.CASCADE, db_column='IdProducto')

    class Meta:
        db_table = 'detalleDePedidos'

class Asistencias(models.Model):
    idasistencia = models.AutoField(db_column='IdAsistencia', primary_key=True)
    fechaasistencia = models.DateField(db_column='FechaAsistencia')
    horaentrada = models.TimeField(db_column='HoraEntrada')
    horasalida = models.TimeField(db_column='HoraSalida', null=True, blank=True)
    idempleado = models.ForeignKey(Empleados, on_delete=models.CASCADE, db_column='IdEmpleado')
    rol = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True, help_text="Rol con el que se registró esta asistencia")

    class Meta:
        db_table = 'asistencias'

class Horario(models.Model):
    idhorario = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleados, on_delete=models.CASCADE, related_name="horarios")
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="horarios", null=True)
    dia_semana = models.IntegerField()  # Lunes=0, Domingo=6
    semana_del_mes = models.IntegerField(default=1) # 1, 2, 3, 4
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    class Meta:
        db_table = 'horarios'
        verbose_name = "Horario"
        verbose_name_plural = "Horarios"

    def __str__(self):
        return f"Turno de {self.empleado} para el rol {self.rol.nombrerol if self.rol else ''}"
    

class Movimientosdecaja(models.Model):
    idmovcaja = models.AutoField(db_column='IdMovCaja', primary_key=True)
    nombreusuariomovcaja = models.CharField(db_column='NombreUsuarioMovCaja', max_length=50)
    fechamovcaja = models.DateField(db_column='FechaMovCaja')
    horamovcaja = models.TimeField(db_column='HoraMovCaja')
    nombrecajamovcaja = models.CharField(db_column='NombreCajaMovCaja', max_length=50)
    tipomovcaja = models.CharField(db_column='TipoMovCaja', max_length=50)
    conceptomovcaja = models.CharField(db_column='ConceptoMovCaja', max_length=50)
    valormovcaja = models.FloatField(db_column='ValorMovCaja')
    saldomovcaja = models.FloatField(db_column='SaldoMovCaja')
    idusuarios = models.ForeignKey('Usuarios', on_delete=models.CASCADE, db_column='IdUsuarios', null=True, blank=True)
    idcaja = models.ForeignKey('Caja', on_delete=models.CASCADE, db_column='IdCaja', null=True, blank=True)

    class Meta:
        db_table = 'movimientosdecaja'

#nombredeapp
#Tablas para Gestion de Nominas

class PeriodoNomina(models.Model):
    """Registra los períodos de nómina semanales"""
    idperiodo = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cerrado = models.BooleanField(default=False)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'periodos_nomina'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Período {self.fecha_inicio} - {self.fecha_fin}"


class DeudaNomina(models.Model):
    """Acumula la deuda total de cada empleado"""
    iddeuda = models.AutoField(primary_key=True)
    empleado = models.OneToOneField(Empleados, on_delete=models.CASCADE, related_name='deuda_nomina')
    total_adeudado = models.FloatField(default=0.0)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deuda_nomina'
    
    def __str__(self):
        return f"Deuda de {self.empleado.idusuarios.nombreusuario}: ${self.total_adeudado}"


class RegistroNominaSemanal(models.Model):
    """Registra el resumen de cada semana antes de cerrarla"""
    idregistro = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleados, on_delete=models.CASCADE)
    periodo = models.ForeignKey(PeriodoNomina, on_delete=models.CASCADE)
    rol = models.ForeignKey(Roles, on_delete=models.SET_NULL, null=True, blank=True)
    horas_trabajadas = models.FloatField(default=0.0)
    monto_devengado = models.FloatField(default=0.0)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'registro_nomina_semanal'
        unique_together = ['empleado', 'periodo', 'rol']


class PagoNomina(models.Model):
    """Registra los pagos realizados a empleados"""
    idpago = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleados, on_delete=models.CASCADE)
    monto = models.FloatField()
    metodo_pago = models.CharField(max_length=50, choices=[
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Cheque', 'Cheque'),
    ])
    fecha_pago = models.DateTimeField(auto_now_add=True)
    usuario_registro = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True)
    observacion = models.TextField(blank=True)
    comprobante = models.CharField(max_length=100, blank=True)  # Número de comprobante
    
    class Meta:
        db_table = 'pagos_nomina'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago ${self.monto} a {self.empleado.idusuarios.nombreusuario}"
#Fin
