from django.contrib import admin

from .models import CategoriaTransaccion, Cliente, Cuenta, Transaccion


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'fecha_registro')
    search_fields = ('nombre', 'email')
    list_filter = ('fecha_registro',)


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ('numero_cuenta', 'cliente', 'tipo_cuenta', 'saldo', 'activa')
    list_filter = ('tipo_cuenta', 'activa')
    search_fields = ('numero_cuenta', 'cliente__nombre')


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'tipo', 'monto', 'fecha', 'cuenta_destino')
    list_filter = ('tipo', 'fecha')
    search_fields = ('cuenta__numero_cuenta', 'descripcion')
    filter_horizontal = ('categorias',)


@admin.register(CategoriaTransaccion)
class CategoriaTransaccionAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
