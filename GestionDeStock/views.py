# GestionDeStock/views.py
from django.shortcuts import render

def dashboard(request):
    return render(request, "GestionDeStock/index.html")
