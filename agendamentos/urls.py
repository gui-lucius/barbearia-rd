from django.urls import path
from .views import criar_agendamento, horarios_ocupados, home, horarios_bloqueados
from django.shortcuts import render

def calendario(request):
    return render(request, 'calendario.html')

urlpatterns = [
    path('', home, name='home'),  
    path('api/agendamentos/', criar_agendamento, name='criar_agendamento'),  
    path('api/horarios/', horarios_ocupados, name='horarios_ocupados'),  
    path('api/bloqueios/', horarios_bloqueados, name='horarios_bloqueados'),  
    path('calendario/', calendario, name='calendario'),
]
