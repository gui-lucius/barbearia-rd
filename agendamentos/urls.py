from django.urls import path
from .views import criar_agendamento, horarios_ocupados

urlpatterns = [
    path('api/agendamentos/', criar_agendamento, name='criar_agendamento'),
    path('api/horarios/', horarios_ocupados, name='horarios_ocupados'),
]
