from rest_framework import serializers
from .models import (
    Codigopostal, Ubicaciones, Sucursales, Proveedores, Categorias,
    Productos, Inventarios, Provxprod, Provxsuc, Roles, Usuarios,
    UsuxRoles, Empleados, EmpxSuc, UsuxSuc, Caja, Compras,
    DetalleDeCompras, Ofertas, Ventas, DetalleDeVentas, Pedidos,
    DetalleDePedidos, Asistencias, Horario, Movimientosdecaja
)


class CodigopostalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Codigopostal
        fields = '__all__'


class UbicacionesSerializer(serializers.ModelSerializer):
    codigo_postal = CodigopostalSerializer(source='idcodigopostal', read_only=True)
    
    class Meta:
        model = Ubicaciones
        fields = '__all__'


class SucursalesSerializer(serializers.ModelSerializer):
    ubicacion = UbicacionesSerializer(source='idubicacion', read_only=True)
    
    class Meta:
        model = Sucursales
        fields = '__all__'


class ProveedoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedores
        fields = '__all__'


class CategoriasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorias
        fields = '__all__'


class ProductosSerializer(serializers.ModelSerializer):
    categoria = CategoriasSerializer(source='idcategoria', read_only=True)
    
    class Meta:
        model = Productos
        fields = '__all__'


class InventariosSerializer(serializers.ModelSerializer):
    producto_info = ProductosSerializer(source='producto', read_only=True)
    sucursal_info = SucursalesSerializer(source='sucursal', read_only=True)
    
    class Meta:
        model = Inventarios
        fields = '__all__'


class ProvxprodSerializer(serializers.ModelSerializer):
    proveedor_info = ProveedoresSerializer(source='idproveedor', read_only=True)
    producto_info = ProductosSerializer(source='idproducto', read_only=True)
    
    class Meta:
        model = Provxprod
        fields = '__all__'


class ProvxsucSerializer(serializers.ModelSerializer):
    proveedor_info = ProveedoresSerializer(source='idproveedor', read_only=True)
    sucursal_info = SucursalesSerializer(source='idsucursal', read_only=True)
    
    class Meta:
        model = Provxsuc
        fields = '__all__'


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class UsuariosSerializer(serializers.ModelSerializer):
    roles_info = RolesSerializer(source='roles', many=True, read_only=True)
    
    class Meta:
        model = Usuarios
        fields = '__all__'
        extra_kwargs = {
            'passwordusuario': {'write_only': True}
        }
    
    def create(self, validated_data):
        # Hash de contraseña al crear usuario
        from django.contrib.auth.hashers import make_password
        validated_data['passwordusuario'] = make_password(validated_data['passwordusuario'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Hash de contraseña al actualizar si se proporciona
        if 'passwordusuario' in validated_data:
            from django.contrib.auth.hashers import make_password
            validated_data['passwordusuario'] = make_password(validated_data['passwordusuario'])
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer para login seguro"""
    usuario = serializers.CharField(max_length=50, required=True)
    password = serializers.CharField(max_length=255, required=True, write_only=True)


class UsuxRolesSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    rol_info = RolesSerializer(source='idroles', read_only=True)
    
    class Meta:
        model = UsuxRoles
        fields = '__all__'


class EmpleadosSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    
    class Meta:
        model = Empleados
        fields = '__all__'


class EmpxSucSerializer(serializers.ModelSerializer):
    empleado_info = EmpleadosSerializer(source='idempleado', read_only=True)
    sucursal_info = SucursalesSerializer(source='idsucursal', read_only=True)
    
    class Meta:
        model = EmpxSuc
        fields = '__all__'


class UsuxSucSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuario', read_only=True)
    sucursal_info = SucursalesSerializer(source='idsucursal', read_only=True)
    
    class Meta:
        model = UsuxSuc
        fields = '__all__'


class CajaSerializer(serializers.ModelSerializer):
    sucursal_info = SucursalesSerializer(source='idsucursal', read_only=True)
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    
    class Meta:
        model = Caja
        fields = '__all__'


class ComprasSerializer(serializers.ModelSerializer):
    proveedor_info = ProveedoresSerializer(source='idproveedor', read_only=True)
    caja_info = CajaSerializer(source='idcaja', read_only=True)
    
    class Meta:
        model = Compras
        fields = '__all__'


class DetalleDeComprasSerializer(serializers.ModelSerializer):
    compra_info = ComprasSerializer(source='idcompras', read_only=True)
    producto_info = ProductosSerializer(source='idproducto', read_only=True)
    
    class Meta:
        model = DetalleDeCompras
        fields = '__all__'


class OfertasSerializer(serializers.ModelSerializer):
    producto_info = ProductosSerializer(source='idproducto', read_only=True)
    
    class Meta:
        model = Ofertas
        fields = '__all__'


class VentasSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    oferta_info = OfertasSerializer(source='idofertas', read_only=True)
    caja_info = CajaSerializer(source='idcaja', read_only=True)
    
    class Meta:
        model = Ventas
        fields = '__all__'


class DetalleDeVentasSerializer(serializers.ModelSerializer):
    venta_info = VentasSerializer(source='idventa', read_only=True)
    producto_info = ProductosSerializer(source='idproducto', read_only=True)
    
    class Meta:
        model = DetalleDeVentas
        fields = '__all__'


class PedidosSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    sucursal_info = SucursalesSerializer(source='idsucursal', read_only=True)
    
    class Meta:
        model = Pedidos
        fields = '__all__'


class DetalleDePedidosSerializer(serializers.ModelSerializer):
    pedido_info = PedidosSerializer(source='idpedidos', read_only=True)
    producto_info = ProductosSerializer(source='idproducto', read_only=True)
    
    class Meta:
        model = DetalleDePedidos
        fields = '__all__'


class AsistenciasSerializer(serializers.ModelSerializer):
    empleado_info = EmpleadosSerializer(source='idempleado', read_only=True)
    rol_info = RolesSerializer(source='rol', read_only=True)
    
    class Meta:
        model = Asistencias
        fields = '__all__'


class HorarioSerializer(serializers.ModelSerializer):
    empleado_info = EmpleadosSerializer(source='empleado', read_only=True)
    rol_info = RolesSerializer(source='rol', read_only=True)
    
    class Meta:
        model = Horario
        fields = '__all__'


class MovimientosdecajaSerializer(serializers.ModelSerializer):
    usuario_info = UsuariosSerializer(source='idusuarios', read_only=True)
    caja_info = CajaSerializer(source='idcaja', read_only=True)
    
    class Meta:
        model = Movimientosdecaja
        fields = '__all__'