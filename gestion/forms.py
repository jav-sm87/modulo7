from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Cliente, Cuenta, Transaccion


class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ('numero_cuenta', 'tipo_cuenta')
        widgets = {
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cuenta': forms.Select(attrs={'class': 'form-control'}),
        }


class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ('tipo', 'monto', 'descripcion', 'cuenta_destino', 'categorias')
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'cuenta_destino': forms.Select(attrs={'class': 'form-control'}),
            'categorias': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, cuenta_origen=None, **kwargs):
        super().__init__(*args, **kwargs)
        if cuenta_origen is not None:
            self.fields['cuenta_destino'].queryset = Cuenta.objects.filter(
                activa=True,
            ).exclude(pk=cuenta_origen.pk)
        self.fields['cuenta_destino'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cuenta_destino = cleaned_data.get('cuenta_destino')
        if tipo == Transaccion.TRANSFERENCIA and not cuenta_destino:
            raise forms.ValidationError('Debes seleccionar una cuenta destino para transferir.')
        return cleaned_data
