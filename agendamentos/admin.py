# agendamentos/admin.py

from django.contrib import admin
from django.utils import timezone

from .models import (
    Agendamento,
    HorarioBloqueado,
    BloqueioPeriodo,
    ReservaPeriodo,
)


# -------------------------------------------------
# Helpers de formatação (só pra ficar bonito no admin)
# -------------------------------------------------
def format_dt(dt):
    if not dt:
        return "-"
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%d/%m/%Y %H:%M")


# -------------------------------------------------
# HORÁRIOS BLOQUEADOS (slots individuais)
# -------------------------------------------------
@admin.register(HorarioBloqueado)
class HorarioBloqueadoAdmin(admin.ModelAdmin):
    list_display = ("data_formatada", "motivo", "bloqueio_periodo")
    list_filter = ("data_horario",)
    search_fields = ("motivo",)
    ordering = ("-data_horario",)

    def data_formatada(self, obj):
        return format_dt(obj.data_horario)

    data_formatada.short_description = "Data / Hora"


# -------------------------------------------------
# AGENDAMENTOS (clientes)
# -------------------------------------------------
@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_cliente",
        "data_formatada",
        "status",
        "disponivel",
        "reserva_periodo",
    )

    list_filter = (
        "status",
        "disponivel",
        "data_horario_reserva",
    )

    search_fields = (
        "nome_cliente",
        "email_cliente",
    )

    readonly_fields = ("disponivel",)

    ordering = ("-data_horario_reserva",)

    fieldsets = (
        ("Cliente", {
            "fields": ("nome_cliente", "email_cliente"),
        }),
        ("Agendamento", {
            "fields": ("data_horario_reserva", "status", "disponivel"),
        }),
        ("Origem", {
            "fields": ("reserva_periodo",),
        }),
    )

    def data_formatada(self, obj):
        return format_dt(obj.data_horario_reserva)

    data_formatada.short_description = "Data / Hora"


# -------------------------------------------------
# BLOQUEIO POR PERÍODO (ADMIN MASTER)
# -------------------------------------------------
@admin.register(BloqueioPeriodo)
class BloqueioPeriodoAdmin(admin.ModelAdmin):
    list_display = (
        "inicio_formatado",
        "fim_formatado",
        "motivo",
        "total_slots",
    )

    list_filter = ("inicio",)
    search_fields = ("motivo",)
    ordering = ("-inicio",)

    fieldsets = (
        ("Período de Bloqueio", {
            "fields": ("inicio", "fim"),
            "description": (
                "Bloqueia automaticamente todos os horários de 1h "
                "entre o início e o fim."
            ),
        }),
        ("Informações", {
            "fields": ("motivo",),
        }),
    )

    def inicio_formatado(self, obj):
        return format_dt(obj.inicio)

    def fim_formatado(self, obj):
        return format_dt(obj.fim)

    def total_slots(self, obj):
        return obj.slots.count()

    inicio_formatado.short_description = "Início"
    fim_formatado.short_description = "Fim"
    total_slots.short_description = "Slots criados"


# -------------------------------------------------
# RESERVA POR PERÍODO (ADMIN)
# -------------------------------------------------
@admin.register(ReservaPeriodo)
class ReservaPeriodoAdmin(admin.ModelAdmin):
    list_display = (
        "inicio_formatado",
        "fim_formatado",
        "titulo",
        "total_agendamentos",
    )

    list_filter = ("inicio",)
    search_fields = ("titulo", "observacao")
    ordering = ("-inicio",)

    fieldsets = (
        ("Período Reservado", {
            "fields": ("inicio", "fim"),
            "description": (
                "Cria automaticamente agendamentos CONFIRMADOS "
                "de 1h em 1h para este período."
            ),
        }),
        ("Detalhes", {
            "fields": ("titulo", "observacao"),
        }),
    )

    def inicio_formatado(self, obj):
        return format_dt(obj.inicio)

    def fim_formatado(self, obj):
        return format_dt(obj.fim)

    def total_agendamentos(self, obj):
        return obj.agendamentos.count()

    inicio_formatado.short_description = "Início"
    fim_formatado.short_description = "Fim"
    total_agendamentos.short_description = "Agendamentos criados"
