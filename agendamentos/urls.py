from django.urls import path
from .views import criar_agendamento, horarios_ocupados, home

urlpatterns = [
    path('', home, name='home'),  # Página inicial (renderiza index.html)
    path('api/agendamentos/', criar_agendamento, name='criar_agendamento'),  # Rota para criar agendamento
    path('api/horarios/', horarios_ocupados, name='horarios_ocupados'),  # Rota para ver horários ocupados
]
