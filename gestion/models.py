from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class Cliente(models.Model):
    """Perfil financiero de un usuario. Relacion Uno a Uno con auth.User."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cliente',
    )
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Ingresa un telefono valido.')],
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Cuenta(models.Model):
    """Cuenta digital de un cliente. Relacion Muchos a Uno con Cliente."""

    TIPO_CORRIENTE = 'CORRIENTE'
    TIPO_AHORRO = 'AHORRO'
    TIPO_CHOICES = [
        (TIPO_CORRIENTE, 'Cuenta Corriente'),
        (TIPO_AHORRO, 'Cuenta de Ahorro'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='cuentas',
    )
    numero_cuenta = models.CharField(max_length=20, unique=True)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_AHORRO)
    saldo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.numero_cuenta} ({self.cliente.nombre})'


class CategoriaTransaccion(models.Model):
    """Etiqueta reutilizable para clasificar transacciones (Muchos a Muchos)."""

    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = 'Categorias de transaccion'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Transaccion(models.Model):
    """Movimiento sobre una cuenta. Relacion Muchos a Uno con Cuenta y
    Muchos a Muchos con CategoriaTransaccion."""

    DEPOSITO = 'DEPOSITO'
    RETIRO = 'RETIRO'
    TRANSFERENCIA = 'TRANSFERENCIA'
    TIPO_CHOICES = [
        (DEPOSITO, 'Deposito'),
        (RETIRO, 'Retiro'),
        (TRANSFERENCIA, 'Transferencia'),
    ]

    cuenta = models.ForeignKey(
        Cuenta,
        on_delete=models.CASCADE,
        related_name='transacciones',
    )
    cuenta_destino = models.ForeignKey(
        Cuenta,
        on_delete=models.SET_NULL,
        related_name='transacciones_recibidas',
        blank=True,
        null=True,
        help_text='Solo aplica para transferencias entre cuentas.',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=DEPOSITO)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255, blank=True)
    categorias = models.ManyToManyField(
        CategoriaTransaccion,
        blank=True,
        related_name='transacciones',
    )

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} de {self.monto} en {self.cuenta.numero_cuenta}'
