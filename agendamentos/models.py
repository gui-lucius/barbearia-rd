from django.db import models
from django.core.mail import send_mail
from django.utils.timezone import make_aware, localtime
from django.core.exceptions import ValidationError

class HorarioBloqueado(models.Model):
    data_horario = models.DateTimeField(unique=True)  # O horário que será bloqueado
    motivo = models.CharField(max_length=255, blank=True, null=True)  # O barbeiro pode anotar um motivo opcional

    def __str__(self):
        return f"Bloqueado: {localtime(self.data_horario).strftime('%d/%m/%Y %H:%M')}"


class Agendamento(models.Model):
    nome_cliente = models.CharField(max_length=100)
    email_cliente = models.EmailField(null=True, blank=True)
    data_horario_reserva = models.DateTimeField()

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('recusado', 'Recusado'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')

    # ✅ Novo campo para bloquear horários
    disponivel = models.BooleanField(default=True)  # Se False, o horário está fechado

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['data_horario_reserva'], name='unique_agendamento_horario')
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            old_status = Agendamento.objects.get(pk=self.pk).status
            if old_status != self.status:
                if self.status == "recusado":
                    self.delete()  # 🔴 Se for recusado, deleta o agendamento
                    return
                self.enviar_email()
        super().save(*args, **kwargs)

    def enviar_email(self):
        if self.email_cliente:
            assunto = "Confirmação de Agendamento" if self.status == "aceito" else "Agendamento Recusado"
            mensagem = f"Olá {self.nome_cliente}, seu agendamento foi {self.status}!"
            try:
                send_mail(assunto, mensagem, 'seuemail@gmail.com', [self.email_cliente], fail_silently=True)
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")

    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            status = "Disponível" if self.disponivel else "Fechado"
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')} ({status})"
        return f"{self.nome_cliente} - (Sem data)"
