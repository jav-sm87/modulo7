from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection, transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormView

from .forms import CuentaForm, RegistroUsuarioForm, TransaccionForm
from .models import Cliente, Cuenta, Transaccion


class RegistroUsuarioView(FormView):
    """Crea un User + su Cliente asociado (relacion Uno a Uno)."""

    template_name = 'registration/registro.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('cuenta_list')

    def form_valid(self, form):
        usuario = form.save()
        Cliente.objects.create(
            usuario=usuario,
            nombre=usuario.username,
            email=form.cleaned_data['email'],
            telefono=form.cleaned_data.get('telefono', ''),
        )
        login(self.request, usuario)
        messages.success(self.request, 'Cuenta creada correctamente. ¡Bienvenido a Alke Wallet!')
        return super().form_valid(form)


class ClienteCuentasMixin(LoginRequiredMixin):
    """Restringe cualquier vista a las cuentas del cliente autenticado."""

    def get_cliente(self):
        # Los usuarios creados con createsuperuser (u otros flujos fuera de
        # /registro/) no tienen Cliente asociado todavia: se crea uno la
        # primera vez que acceden, en vez de devolver un 404.
        cliente, _ = Cliente.objects.get_or_create(
            usuario=self.request.user,
            defaults={
                'nombre': self.request.user.get_full_name() or self.request.user.username,
                'email': self.request.user.email or f'{self.request.user.username}@alkewallet.local',
            },
        )
        return cliente


class CuentaListView(ClienteCuentasMixin, ListView):
    model = Cuenta
    template_name = 'gestion/cuenta_list.html'
    context_object_name = 'cuentas'

    def get_queryset(self):
        return Cuenta.objects.filter(cliente=self.get_cliente()).annotate(
            total_transacciones=Count('transacciones'),
        )


class CuentaDetailView(ClienteCuentasMixin, DetailView):
    model = Cuenta
    template_name = 'gestion/cuenta_detail.html'
    context_object_name = 'cuenta'

    def get_queryset(self):
        return Cuenta.objects.filter(cliente=self.get_cliente())


class CuentaCreateView(ClienteCuentasMixin, CreateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'gestion/cuenta_form.html'

    def form_valid(self, form):
        form.instance.cliente = self.get_cliente()
        messages.success(self.request, 'Cuenta creada correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('cuenta_detail', kwargs={'pk': self.object.pk})


class CuentaUpdateView(ClienteCuentasMixin, UpdateView):
    model = Cuenta
    form_class = CuentaForm
    template_name = 'gestion/cuenta_form.html'

    def get_queryset(self):
        return Cuenta.objects.filter(cliente=self.get_cliente())

    def form_valid(self, form):
        messages.success(self.request, 'Cuenta actualizada correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('cuenta_detail', kwargs={'pk': self.object.pk})


class CuentaDeleteView(ClienteCuentasMixin, DeleteView):
    model = Cuenta
    template_name = 'gestion/cuenta_confirm_delete.html'
    success_url = reverse_lazy('cuenta_list')

    def get_queryset(self):
        return Cuenta.objects.filter(cliente=self.get_cliente())

    def form_valid(self, form):
        messages.success(self.request, 'Cuenta eliminada correctamente.')
        return super().form_valid(form)


class TransaccionListView(ClienteCuentasMixin, ListView):
    model = Transaccion
    template_name = 'gestion/transaccion_list.html'
    context_object_name = 'transacciones'

    def get_cuenta(self):
        return get_object_or_404(Cuenta, pk=self.kwargs['cuenta_pk'], cliente=self.get_cliente())

    def get_queryset(self):
        self.cuenta = self.get_cuenta()
        return (
            Transaccion.objects.filter(cuenta=self.cuenta)
            .select_related('cuenta_destino')
            .prefetch_related('categorias')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuenta'] = self.cuenta
        return context


class TransaccionCreateView(ClienteCuentasMixin, CreateView):
    model = Transaccion
    form_class = TransaccionForm
    template_name = 'gestion/transaccion_form.html'

    def get_cuenta(self):
        return get_object_or_404(Cuenta, pk=self.kwargs['cuenta_pk'], cliente=self.get_cliente())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['cuenta_origen'] = self.get_cuenta()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuenta'] = self.get_cuenta()
        return context

    def form_valid(self, form):
        cuenta = self.get_cuenta()
        monto = form.cleaned_data['monto']
        tipo = form.cleaned_data['tipo']

        if tipo in (Transaccion.RETIRO, Transaccion.TRANSFERENCIA) and monto > cuenta.saldo:
            form.add_error('monto', 'Saldo insuficiente para realizar esta operacion.')
            return self.form_invalid(form)

        with transaction.atomic():
            form.instance.cuenta = cuenta
            response = super().form_valid(form)

            if tipo == Transaccion.DEPOSITO:
                cuenta.saldo = Decimal(cuenta.saldo) + monto
            elif tipo == Transaccion.RETIRO:
                cuenta.saldo = Decimal(cuenta.saldo) - monto
            elif tipo == Transaccion.TRANSFERENCIA:
                destino = form.cleaned_data['cuenta_destino']
                cuenta.saldo = Decimal(cuenta.saldo) - monto
                destino.saldo = Decimal(destino.saldo) + monto
                destino.save()
            cuenta.save()

        messages.success(self.request, 'Transaccion registrada correctamente.')
        return response

    def get_success_url(self):
        return reverse('transaccion_list', kwargs={'cuenta_pk': self.object.cuenta.pk})


class ReporteClienteView(ClienteCuentasMixin, ListView):
    """Consultas personalizadas: filter/annotate del ORM + SQL crudo (raw y cursor)."""

    template_name = 'gestion/reporte.html'
    context_object_name = 'cuentas'

    def get_queryset(self):
        cliente = self.get_cliente()
        return (
            Cuenta.objects.filter(cliente=cliente, activa=True)
            .annotate(
                num_transacciones=Count('transacciones'),
                total_depositado=Sum(
                    'transacciones__monto',
                    filter=Q(transacciones__tipo=Transaccion.DEPOSITO),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.get_cliente()

        # Consulta SQL personalizada con raw()
        cuentas_raw = Cuenta.objects.raw(
            'SELECT * FROM gestion_cuenta WHERE cliente_id = %s AND saldo > %s',
            [cliente.pk, 0],
        )
        context['cuentas_con_saldo'] = list(cuentas_raw)

        # Consulta directa con cursor
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM gestion_transaccion t '
                'INNER JOIN gestion_cuenta c ON t.cuenta_id = c.id '
                'WHERE c.cliente_id = %s',
                [cliente.pk],
            )
            total_transacciones = cursor.fetchone()[0]
        context['total_transacciones'] = total_transacciones
        return context
