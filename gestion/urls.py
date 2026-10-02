from django.urls import path

from . import views

urlpatterns = [
    path('registro/', views.RegistroUsuarioView.as_view(), name='registro'),

    path('cuentas/', views.CuentaListView.as_view(), name='cuenta_list'),
    path('cuentas/nueva/', views.CuentaCreateView.as_view(), name='cuenta_create'),
    path('cuentas/<int:pk>/', views.CuentaDetailView.as_view(), name='cuenta_detail'),
    path('cuentas/<int:pk>/editar/', views.CuentaUpdateView.as_view(), name='cuenta_update'),
    path('cuentas/<int:pk>/eliminar/', views.CuentaDeleteView.as_view(), name='cuenta_delete'),

    path('cuentas/<int:cuenta_pk>/transacciones/', views.TransaccionListView.as_view(), name='transaccion_list'),
    path(
        'cuentas/<int:cuenta_pk>/transacciones/nueva/',
        views.TransaccionCreateView.as_view(),
        name='transaccion_create',
    ),

    path('reporte/', views.ReporteClienteView.as_view(), name='reporte'),
]
