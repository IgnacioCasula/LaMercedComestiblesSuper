from django.shortcuts import render

def gestion_de_stock(request):
    return render(request, 'GestionDeStock/index.html')
