from django.contrib import admin
from .models import Agendamento

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_cliente', 'data_horario_reserva', 'status')  # Campos exibidos na lista
    list_filter = ('status', 'data_horario_reserva')  # Filtros laterais
    search_fields = ('nome_cliente', 'email_cliente')  # Campos pesquisáveis
