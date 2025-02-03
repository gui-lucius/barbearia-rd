from django.urls import path
from .views import criar_agendamento, horarios_ocupados, home  # Importamos a nova view

urlpatterns = [
    path('', home, name='home'),  # Definimos a rota inicial
    path('api/agendamentos/', criar_agendamento, name='criar_agendamento'),
    path('api/horarios/', horarios_ocupados, name='horarios_ocupados'),
]
