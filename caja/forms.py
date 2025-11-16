from django import forms
from .models import Caja

class AperturaCajaForm(forms.ModelForm):
    """
    Form para apertura: expone montoinicialcaja y observacionapertura.
    Validación clave: montoinicialcaja >= 0.
    """
    class Meta:
        model = Caja
        fields = ["montoinicialcaja", "observacionapertura"]
        widgets = {
            "montoinicialcaja": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "0.00",
                "step": "0.01",
                "min": "0"
            }),
            "observacionapertura": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Turno, cajero, notas..."
            }),
        }

    def clean_montoinicialcaja(self):
        monto = self.cleaned_data.get("montoinicialcaja", 0)
        if monto is None or monto < 0:
            raise forms.ValidationError("El monto inicial no puede ser negativo.")
        return monto