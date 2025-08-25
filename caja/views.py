from django.shortcuts import render
from caja.models import *
from .forms import *
# Create your views here.
def hola(request):
    return render(request, 'index.html')

def ingresarmontoini(request):
    Montoini = Cajas.montoinicialcaja()
