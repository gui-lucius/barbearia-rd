from django.urls import path
from .views import criar_agendamento, horarios_ocupados, home, horarios_bloqueados  # ✅ Adicionado horarios_bloqueados
from django.shortcuts import render

def calendario(request):
    return render(request, 'calendario.html')

urlpatterns = [
    path('', home, name='home'),  # Página inicial (renderiza index.html)
    path('api/agendamentos/', criar_agendamento, name='criar_agendamento'),  # Rota para criar agendamento
    path('api/horarios/', horarios_ocupados, name='horarios_ocupados'),  # Rota para ver horários ocupados
    path('api/bloqueios/', horarios_bloqueados, name='horarios_bloqueados'),  # ✅ Nova rota para horários bloqueados
    path('calendario/', calendario, name='calendario'),
]
