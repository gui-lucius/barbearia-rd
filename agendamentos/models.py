from django.db import models
from django.core.mail import send_mail
from django.utils.timezone import make_aware, localtime
from django.core.exceptions import ValidationError

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

    from django.utils.timezone import localtime

    def enviar_email(self):
        print(f"Enviando e-mail para {self.email_cliente} sobre o status {self.status}")  # Debug
        if self.email_cliente:
            assunto = "Confirmação de Agendamento" if self.status == "aceito" else "Agendamento Recusado"
            mensagem = (
                f"📅 Olá {self.nome_cliente}, seu agendamento foi {self.status}!\n\n"
                f"📆 Data: {localtime(self.data_horario_reserva).strftime('%d/%m/%Y')}\n"
                f"🕒 Hora: {localtime(self.data_horario_reserva).strftime('%H:%M')}\n\n"
                "Se tiver dúvidas, me chama!\n\n"
                "📍 Denis Barbearia"
            )

            try:
                send_mail(
                    assunto,
                    mensagem,
                    'denisbarbeariard@gmail.com',
                    [self.email_cliente],
                    fail_silently=False  # Se der erro, vai mostrar no console
                )
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")



    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')}"
        return f"{self.nome_cliente} - (Sem data)"
