from django.contrib import admin
from .models import Agendamento
from .models import HorarioBloqueado


@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ('data_horario', 'motivo')  # Exibe os horários bloqueados no painel
    search_fields = ('data_horario', 'motivo')


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_cliente', 'data_horario_reserva', 'status', 'disponivel')  # ✅ Adiciona o campo "disponivel"
    list_filter = ('status', 'data_horario_reserva', 'disponivel')  # ✅ Filtro para horários disponíveis
    search_fields = ('nome_cliente', 'email_cliente')

    actions = ["trancar_horarios", "destrancar_horarios"]  # ✅ Ações rápidas no Django Admin

    @admin.action(description="Trancar horários selecionados")
    def trancar_horarios(self, request, queryset):
        queryset.update(disponivel=False)

    @admin.action(description="Destrancar horários selecionados")
    def destrancar_horarios(self, request, queryset):
        queryset.update(disponivel=True)
