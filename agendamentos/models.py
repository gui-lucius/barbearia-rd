from django.db import models
from django.core.mail import send_mail
from django.utils.timezone import make_aware, localtime

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
            old_status = Agendamento.objects.filter(pk=self.pk).values_list("status", flat=True).first()
            if old_status and old_status != self.status:
                if self.status == "recusado":
                    self.__class__.objects.filter(pk=self.pk).delete()  # 🔴 Isso evita chamadas extras do Django
                    return
            
                self.enviar_email()
    
    super().save(*args, **kwargs)



    def enviar_email(self):
        if self.email_cliente:
            # Formata a data e hora corretamente
            data_horario_formatado = localtime(self.data_horario_reserva).strftime('%d/%m/%Y')
            hora_formatada = localtime(self.data_horario_reserva).strftime('%H:%M')

            # Define o assunto do e-mail
            assunto = "Confirmação de Agendamento" if self.status == "aceito" else "Agendamento Recusado"

            # Mensagem personalizada para o cliente
            mensagem = (
                f"Olá {self.nome_cliente}, seu agendamento foi {self.status}!\n\n"
                f"📅 Dia: {data_horario_formatado}\n"
                f"🕒 Hora: {hora_formatada}\n\n"
                "Fico no seu aguardo, até logo!"
            )

            # Envia o e-mail
            try:
                send_mail(
                    assunto,
                    mensagem,
                    'denisbarbeariard@gmail.com',  # 🔴 Certifique-se de que esse e-mail está configurado corretamente no Django
                    [self.email_cliente],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")

    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')}"
        return f"{self.nome_cliente} - (Sem data)"
