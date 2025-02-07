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
            # Formatar data e horário corretamente
            data_formatada = localtime(self.data_horario_reserva).strftime('%d/%m/%Y')
            hora_formatada = localtime(self.data_horario_reserva).strftime('%H:%M')

            # Assunto do e-mail
            if self.status == "aceito":
                assunto = "Seu agendamento foi CONFIRMADO! 🎉"
                mensagem = (
                    f"Olá {self.nome_cliente},\n\n"
                    f"Seu agendamento na **Denis Barbearia** foi **CONFIRMADO**! 🎉\n"
                    f"📅 **Data:** {data_formatada}\n"
                    f"🕒 **Horário:** {hora_formatada}\n\n"
                    "Se precisar reagendar ou tiver dúvidas, entre em contato.\n\n"
                    "Até breve!\n"
                    "📍 Denis Barbearia"
                )
            else:
                assunto = "Infelizmente, seu agendamento foi recusado 😢"
                mensagem = (
                    f"Olá {self.nome_cliente},\n\n"
                    f"Infelizmente, seu agendamento foi **RECUSADO**.\n"
                    f"Se desejar remarcar, entre em contato conosco.\n\n"
                    "Agradecemos sua compreensão.\n"
                    "📍 Denis Barbearia"
                )

            # Enviar e-mail
            try:
                send_mail(
                    assunto,
                    mensagem,
                    'denisbarbeariard@gmail.com',
                    [self.email_cliente],
                    fail_silently=False  # 🔴 Agora vai mostrar erro se falhar
                )
                print(f"✅ E-mail enviado com sucesso para {self.email_cliente}")
            except Exception as e:
                print(f"❌ Erro ao enviar e-mail: {e}")


    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')}"
        return f"{self.nome_cliente} - (Sem data)"
