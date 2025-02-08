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
        enviar_email = False

        if self.pk:  # Se já existe, verifica se o status mudou
            old_status = Agendamento.objects.get(pk=self.pk).status
            if old_status != self.status:
                enviar_email = True
                if self.status == "recusado":
                    self.delete()
                    return

        super().save(*args, **kwargs)

        if enviar_email:
            self.enviar_email()  # Chama o envio do e-mail


    def enviar_email(self):
        if self.email_cliente:
            assunto = "Seu agendamento foi CONFIRMADO! 🎉" if self.status == "aceito" else "Infelizmente, seu agendamento foi recusado 😢"
        
            mensagem_texto = (
                f"Olá {self.nome_cliente},\n\n"
                f"Seu agendamento foi {'CONFIRMADO' if self.status == 'aceito' else 'RECUSADO'}!\n"
                f"Data: {localtime(self.data_horario_reserva).strftime('%d/%m/%Y')}\n"
                f"Horário: {localtime(self.data_horario_reserva).strftime('%H:%M')}\n\n"
                "Se precisar reagendar, entre em contato.\n"
                "Até breve!\n"
                "Denis Barbearia"
            )

            mensagem_html = (
                f"<p>Olá <strong>{self.nome_cliente}</strong>,</p>"
                f"<p>Seu agendamento na <strong>Denis Barbearia</strong> foi "
                f"{'<strong style=\"color:green;\">CONFIRMADO! 🎉</strong>' if self.status == 'aceito' else '<strong style=\"color:red;\">RECUSADO 😢</strong>'}</p>"
                f"<p><strong>📅 Data:</strong> {localtime(self.data_horario_reserva).strftime('%d/%m/%Y')}</p>"
                f"<p><strong>🕒 Horário:</strong> {localtime(self.data_horario_reserva).strftime('%H:%M')}</p>"
                "<p>Se precisar reagendar ou tiver dúvidas, entre em contato.</p>"
                "<p>Até breve!</p>"
                "<p>📍 <strong>Denis Barbearia</strong></p>"
            )

            try:
                send_mail(
                    assunto,
                    mensagem_texto,  # Texto puro (fallback)
                    'seuemail@gmail.com',
                    [self.email_cliente],
                    fail_silently=True,
                    html_message=mensagem_html  # Agora permite formatação HTML
                )
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")



    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')}"
        return f"{self.nome_cliente} - (Sem data)"
