from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import CategoriaTransaccion, Cliente, Cuenta, Transaccion


class ModeloClienteCuentaTransaccionTest(TestCase):
    """Valida el ORM: creacion, relaciones y validaciones de los modelos."""

    def setUp(self):
        self.usuario = User.objects.create_user(username='ana', password='clave12345')
        self.cliente = Cliente.objects.create(
            usuario=self.usuario, nombre='Ana Garcia', email='ana@example.com',
        )
        self.cuenta = Cuenta.objects.create(
            cliente=self.cliente, numero_cuenta='CTA-001', saldo=Decimal('100.00'),
        )

    def test_relacion_uno_a_uno_cliente_usuario(self):
        self.assertEqual(self.cliente.usuario, self.usuario)
        self.assertEqual(self.usuario.cliente, self.cliente)

    def test_relacion_muchos_a_uno_cuenta_cliente(self):
        otra_cuenta = Cuenta.objects.create(cliente=self.cliente, numero_cuenta='CTA-002')
        self.assertEqual(self.cliente.cuentas.count(), 2)
        self.assertIn(otra_cuenta, self.cliente.cuentas.all())

    def test_relacion_muchos_a_muchos_transaccion_categoria(self):
        categoria = CategoriaTransaccion.objects.create(nombre='Sueldo')
        transaccion = Transaccion.objects.create(
            cuenta=self.cuenta, tipo=Transaccion.DEPOSITO, monto=Decimal('50.00'),
        )
        transaccion.categorias.add(categoria)
        self.assertIn(categoria, transaccion.categorias.all())
        self.assertIn(transaccion, categoria.transacciones.all())

    def test_crud_actualizar_y_eliminar_cuenta(self):
        self.cuenta.saldo = Decimal('200.00')
        self.cuenta.save()
        self.assertEqual(Cuenta.objects.get(pk=self.cuenta.pk).saldo, Decimal('200.00'))

        pk = self.cuenta.pk
        self.cuenta.delete()
        self.assertFalse(Cuenta.objects.filter(pk=pk).exists())

    def test_consulta_filter_e_istartswith(self):
        Cliente.objects.create(
            usuario=User.objects.create_user(username='luis', password='clave12345'),
            nombre='Luis Perez', email='luis@example.com',
        )
        resultado = Cliente.objects.filter(nombre__istartswith='a')
        self.assertEqual(resultado.count(), 1)
        self.assertEqual(resultado.first().nombre, 'Ana Garcia')

    def test_consulta_raw(self):
        resultados = list(Cuenta.objects.raw(
            'SELECT * FROM gestion_cuenta WHERE saldo > %s', [0],
        ))
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0].numero_cuenta, 'CTA-001')


class CrudViewsTest(TestCase):
    """Valida las vistas CRUD basadas en clases, proteccion CSRF y autenticacion."""

    def setUp(self):
        self.usuario = User.objects.create_user(username='ana', password='clave12345')
        self.cliente = Cliente.objects.create(
            usuario=self.usuario, nombre='Ana Garcia', email='ana@example.com',
        )
        self.client.login(username='ana', password='clave12345')

    def test_crear_cuenta_via_vista(self):
        response = self.client.post(reverse('cuenta_create'), {
            'numero_cuenta': 'CTA-100',
            'tipo_cuenta': Cuenta.TIPO_AHORRO,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Cuenta.objects.filter(numero_cuenta='CTA-100', cliente=self.cliente).exists())

    def test_lista_de_cuentas_requiere_login(self):
        self.client.logout()
        response = self.client.get(reverse('cuenta_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_deposito_actualiza_saldo(self):
        cuenta = Cuenta.objects.create(cliente=self.cliente, numero_cuenta='CTA-200', saldo=Decimal('0'))
        self.client.post(reverse('transaccion_create', kwargs={'cuenta_pk': cuenta.pk}), {
            'tipo': Transaccion.DEPOSITO,
            'monto': '150.00',
            'descripcion': 'Deposito inicial',
            'categorias': [],
        })
        cuenta.refresh_from_db()
        self.assertEqual(cuenta.saldo, Decimal('150.00'))

    def test_retiro_sin_saldo_suficiente_falla(self):
        cuenta = Cuenta.objects.create(cliente=self.cliente, numero_cuenta='CTA-300', saldo=Decimal('10'))
        response = self.client.post(reverse('transaccion_create', kwargs={'cuenta_pk': cuenta.pk}), {
            'tipo': Transaccion.RETIRO,
            'monto': '500.00',
            'descripcion': 'Retiro excesivo',
            'categorias': [],
        })
        cuenta.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(cuenta.saldo, Decimal('10'))

    def test_eliminar_cuenta_via_vista(self):
        cuenta = Cuenta.objects.create(cliente=self.cliente, numero_cuenta='CTA-400')
        response = self.client.post(reverse('cuenta_delete', kwargs={'pk': cuenta.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cuenta.objects.filter(pk=cuenta.pk).exists())

    def test_no_puede_ver_cuenta_de_otro_cliente(self):
        otro_usuario = User.objects.create_user(username='luis', password='clave12345')
        otro_cliente = Cliente.objects.create(usuario=otro_usuario, nombre='Luis Perez', email='luis@example.com')
        cuenta_ajena = Cuenta.objects.create(cliente=otro_cliente, numero_cuenta='CTA-500')

        response = self.client.get(reverse('cuenta_detail', kwargs={'pk': cuenta_ajena.pk}))
        self.assertEqual(response.status_code, 404)
