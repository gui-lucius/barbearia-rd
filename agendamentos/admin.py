from django.contrib import admin
from .models import Agendamento, HorarioBloqueado

@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ('data_horario', 'motivo') 
    search_fields = ('data_horario', 'motivo')

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('nome_cliente', 'data_horario_reserva', 'status', 'disponivel')  
    list_filter = ('status', 'data_horario_reserva', 'disponivel')  
    search_fields = ('nome_cliente', 'email_cliente')

    actions = ["trancar_horarios", "destrancar_horarios"]

    @admin.action(description="Trancar horários selecionados")
    def trancar_horarios(self, request, queryset):
        queryset.update(disponivel=False)

    @admin.action(description="Destrancar horários selecionados")
    def destrancar_horarios(self, request, queryset):
        queryset.update(disponivel=True)
