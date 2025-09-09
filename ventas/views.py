# ventas/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import VentaForm, DetalleVentaFormSet
from .models import Venta

def registrar_venta(request):
    if request.method == "POST":
        venta_form = VentaForm(request.POST)
        detalle_formset = DetalleVentaFormSet(request.POST)

        if venta_form.is_valid() and detalle_formset.is_valid():
            venta = venta_form.save()
            detalles = detalle_formset.save(commit=False)
            for d in detalles:
                d.venta = venta
                d.save()
            messages.success(request, "✅ Venta registrada con éxito")
            return redirect("ventas:registrar")
    else:
        venta_form = VentaForm()
        detalle_formset = DetalleVentaFormSet()

    return render(request, "ventas/registrar_venta.html", {
        "venta_form": venta_form,
        "detalle_formset": detalle_formset,
    })
