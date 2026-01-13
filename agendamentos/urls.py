# agendamentos/urls.py

from django.urls import path
from . import views

app_name = "agendamentos"

urlpatterns = [
    path("", views.home, name="home"),
    path("calendario/", views.calendario, name="calendario"),

    # API
    path("api/agendamentos/", views.criar_agendamento, name="criar_agendamento"),
    path("api/horarios/", views.horarios_ocupados, name="horarios_ocupados"),
    path("api/bloqueios/", views.horarios_bloqueados, name="horarios_bloqueados"),

    # opcional (eventos prontos pro calendário)
    path("api/eventos/", views.eventos_calendario, name="eventos_calendario"),
]
