# agendamentos/models.py

from datetime import timedelta
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .email_service import send_resend_email

logger = logging.getLogger(__name__)


# ---------------------------
# Helpers
# ---------------------------
def _ensure_hour_floor(dt):
    """Arredonda PARA BAIXO para a hora cheia (min/sec/micro = 0)."""
    return dt.replace(minute=0, second=0, microsecond=0)


def _ensure_hour_ceil(dt):
    """
    Arredonda PARA CIMA para a próxima hora cheia.
    Se já está cravado na hora, mantém.
    """
    if dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
        return dt
    base = dt.replace(minute=0, second=0, microsecond=0)
    return base + timedelta(hours=1)


def _iter_hours(start, end):
    """
    Gera datetimes de 1 em 1 hora: [start, end)
    Ex: start=10:00, end=13:00 -> 10:00,11:00,12:00
    """
    cur = start
    while cur < end:
        yield cur
        cur += timedelta(hours=1)


# ---------------------------
# Models
# ---------------------------
class HorarioBloqueado(models.Model):
    """
    Slot individual de bloqueio (1 por hora).
    Pode ser criado manualmente OU automaticamente por um BloqueioPeriodo.
    """
    data_horario = models.DateTimeField(unique=True)
    motivo = models.CharField(max_length=255, blank=True, null=True)

    bloqueio_periodo = models.ForeignKey(
        "BloqueioPeriodo",
        on_delete=models.CASCADE,
        related_name="slots",
        null=True,
        blank=True,
    )

    def __str__(self):
        dt = self.data_horario
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        motivo = f" - {self.motivo}" if self.motivo else ""
        return f"Bloqueado: {dt.strftime('%d/%m/%Y %H:%M')}{motivo}"


class Agendamento(models.Model):
    nome_cliente = models.CharField(max_length=100)
    email_cliente = models.EmailField(null=True, blank=True)
    data_horario_reserva = models.DateTimeField()

    STATUS_PENDENTE = "pendente"
    STATUS_ACEITO = "aceito"
    STATUS_RECUSADO = "recusado"

    STATUS_CHOICES = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_ACEITO, "Aceito"),
        (STATUS_RECUSADO, "Recusado"),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
    )

    disponivel = models.BooleanField(default=True)

    reserva_periodo = models.ForeignKey(
        "ReservaPeriodo",
        on_delete=models.CASCADE,
        related_name="agendamentos",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["data_horario_reserva"],
                name="unique_agendamento_horario",
            )
        ]
        ordering = ["-data_horario_reserva"]

    def clean(self):
        if HorarioBloqueado.objects.filter(data_horario=self.data_horario_reserva).exists():
            raise ValidationError("Esse horário está bloqueado.")

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            old_status = (
                Agendamento.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )

        # regra de disponibilidade:
        # se foi aceito, deixa indisponível (ocupado)
        self.disponivel = self.status != self.STATUS_ACEITO

        super().save(*args, **kwargs)

        # envia email apenas quando houve troca de status (update)
        if old_status is not None and old_status != self.status:
            self.enviar_email_status()

    def enviar_email_status(self):
        """
        Envia email para o CLIENTE quando o barbeiro aceita/recusa.
        Agora via RESEND (API) para funcionar no Railway sem SMTP.
        """
        if not self.email_cliente:
            return

        dt = self.data_horario_reserva
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)

        dt_str = dt.strftime("%d/%m/%Y %H:%M")

        if self.status == self.STATUS_ACEITO:
            assunto = "✅ Agendamento Confirmado - Barbearia RD"
            text = (
                f"Olá {self.nome_cliente},\n\n"
                "Seu agendamento foi CONFIRMADO! Estamos ansiosos para recebê-lo.\n\n"
                f"📅 Data e Hora: {dt_str}\n"
                "📍 Local: Barbearia RD\n\n"
                "Caso precise remarcar, entre em contato conosco.\n\n"
                "Atenciosamente,\n"
                "Equipe Barbearia RD"
            )
            html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.5;">
              <h2>✅ Agendamento Confirmado</h2>
              <p>Olá <strong>{self.nome_cliente}</strong>,</p>
              <p>Seu agendamento foi <strong>CONFIRMADO</strong>! Estamos ansiosos para recebê-lo.</p>
              <p><strong>📅 Data e Hora:</strong> {dt_str}<br/>
                 <strong>📍 Local:</strong> Barbearia RD</p>
              <hr/>
              <p>Caso precise remarcar, entre em contato conosco.</p>
              <p>Atenciosamente,<br/>Equipe Barbearia RD</p>
            </div>
            """
        elif self.status == self.STATUS_RECUSADO:
            assunto = "❌ Agendamento Recusado - Barbearia RD"
            text = (
                f"Olá {self.nome_cliente},\n\n"
                "Infelizmente, não conseguimos confirmar seu agendamento.\n\n"
                "Sugerimos que tente outro horário disponível em nosso calendário.\n\n"
                "Atenciosamente,\n"
                "Equipe Barbearia RD"
            )
            html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.5;">
              <h2>❌ Agendamento Recusado</h2>
              <p>Olá <strong>{self.nome_cliente}</strong>,</p>
              <p>Infelizmente, não conseguimos confirmar seu agendamento.</p>
              <p>Sugerimos que tente outro horário disponível em nosso calendário.</p>
              <hr/>
              <p>Atenciosamente,<br/>Equipe Barbearia RD</p>
            </div>
            """
        else:
            return

        try:
            send_resend_email(
                to_email=self.email_cliente,
                subject=assunto,
                html=html,
                text=text,
            )
            logger.info(
                "Email de status (%s) enviado (Resend) para cliente=%s agendamento_id=%s",
                self.status,
                self.email_cliente,
                self.pk,
            )
        except Exception:
            logger.exception(
                "Falha ao enviar email de status (%s) (Resend) para cliente=%s agendamento_id=%s",
                self.status,
                self.email_cliente,
                self.pk,
            )

    def __str__(self):
        dt = self.data_horario_reserva
        if dt is None:
            return f"{self.nome_cliente} - (Sem data)"
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        return f"{self.nome_cliente} - {dt.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"


class BloqueioPeriodo(models.Model):
    """
    Bloqueia um intervalo (início/fim) e automaticamente cria slots de 1h em HorarioBloqueado.
    - Valida fim > início
    - Arredonda pra hora cheia
    - Se editar, recria os slots
    - Se deletar, apaga todos os slots
    """
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    motivo = models.CharField(max_length=255, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inicio"]

    def clean(self):
        if not self.inicio or not self.fim:
            return

        ini = _ensure_hour_floor(self.inicio)
        fim = _ensure_hour_ceil(self.fim)

        if fim <= ini:
            raise ValidationError("O fim precisa ser maior que o início.")

        for dt in _iter_hours(ini, fim):
            if Agendamento.objects.filter(data_horario_reserva=dt).exists():
                raise ValidationError(
                    f"Conflito: já existe agendamento em {dt.strftime('%d/%m/%Y %H:%M')}."
                )

    def save(self, *args, **kwargs):
        self.inicio = _ensure_hour_floor(self.inicio)
        self.fim = _ensure_hour_ceil(self.fim)

        super().save(*args, **kwargs)

        HorarioBloqueado.objects.filter(bloqueio_periodo=self).delete()

        for dt in _iter_hours(self.inicio, self.fim):
            HorarioBloqueado.objects.get_or_create(
                data_horario=dt,
                defaults={"motivo": self.motivo, "bloqueio_periodo": self},
            )

    def __str__(self):
        ini = self.inicio
        fim = self.fim
        if timezone.is_aware(ini):
            ini = timezone.localtime(ini)
        if timezone.is_aware(fim):
            fim = timezone.localtime(fim)
        return f"Bloqueio {ini.strftime('%d/%m/%Y %H:%M')} → {fim.strftime('%H:%M')}"


class ReservaPeriodo(models.Model):
    """
    Cria vários Agendamentos confirmados (um por hora) via Admin.
    Útil quando o barbeiro quer "marcar na agenda" sem passar pelo site.
    """
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    titulo = models.CharField(max_length=120, default="Reservado (Admin)")
    observacao = models.CharField(max_length=255, blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inicio"]

    def clean(self):
        if not self.inicio or not self.fim:
            return

        ini = _ensure_hour_floor(self.inicio)
        fim = _ensure_hour_ceil(self.fim)

        if fim <= ini:
            raise ValidationError("O fim precisa ser maior que o início.")

        for dt in _iter_hours(ini, fim):
            if HorarioBloqueado.objects.filter(data_horario=dt).exists():
                raise ValidationError(
                    f"Conflito: horário bloqueado em {dt.strftime('%d/%m/%Y %H:%M')}."
                )
            if Agendamento.objects.filter(data_horario_reserva=dt).exists():
                raise ValidationError(
                    f"Conflito: já existe agendamento em {dt.strftime('%d/%m/%Y %H:%M')}."
                )

    def save(self, *args, **kwargs):
        self.inicio = _ensure_hour_floor(self.inicio)
        self.fim = _ensure_hour_ceil(self.fim)

        super().save(*args, **kwargs)

        Agendamento.objects.filter(reserva_periodo=self).delete()

        for dt in _iter_hours(self.inicio, self.fim):
            Agendamento.objects.create(
                nome_cliente=self.titulo,
                email_cliente=None,
                data_horario_reserva=dt,
                status=Agendamento.STATUS_ACEITO,
                disponivel=False,
                reserva_periodo=self,
            )

    def __str__(self):
        ini = self.inicio
        fim = self.fim
        if timezone.is_aware(ini):
            ini = timezone.localtime(ini)
        if timezone.is_aware(fim):
            fim = timezone.localtime(fim)
        return f"Reserva {ini.strftime('%d/%m/%Y %H:%M')} → {fim.strftime('%H:%M')} ({self.titulo})"