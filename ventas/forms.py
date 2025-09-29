# Ruta: LaMercedComestiblesSuper/venta/forms.py
from django import forms

class VentaForm(forms.Form):
    metodo_pago = forms.ChoiceField(
        choices=[
            ('EFECTIVO', 'EFECTIVO'),
            ('TARJETA DEBITO', 'TARJETA DÉBITO'),
            ('TARJETA CREDITO', 'TARJETA CRÉDITO'),
            ('TRANSFERENCIA', 'TRANSFERENCIA'),
        ],
        widget=forms.Select(attrs={
            'class': 'inpt',
            'id': 'metodoPago'
        })
    )

class RecargoForm(forms.Form):
    recargo = forms.DecimalField(
        required=False,
        initial=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'inpt',
            'id': 'recargo',
            'step': '0.01'
        })
    )