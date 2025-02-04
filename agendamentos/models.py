from django.db import models
from django.core.mail import send_mail
from django.utils.timezone import localtime
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
        return f"{self.nome_cliente} - {localtime(self.data_horario_reserva).strftime('%d/%m/%Y %H:%M')}"
