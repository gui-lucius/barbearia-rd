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
        if not self.email_cliente:
            print("⚠️ Nenhum e-mail de cliente cadastrado. E-mail não enviado.")
            return  # Sai da função se o e-mail estiver vazio

        try:
            # Garante que data_horario_reserva não seja None antes de formatar
            if not self.data_horario_reserva:
                raise ValueError("A data e horário do agendamento estão vazios!")

            # Formatando a data e hora corretamente
            data_horario_formatado = localtime(self.data_horario_reserva).strftime('%d/%m/%Y')
            hora_formatada = localtime(self.data_horario_reserva).strftime('%H:%M')

            # Definindo o assunto do e-mail
            assunto = "Confirmação de Agendamento" if self.status == "aceito" else "Agendamento Recusado"

            # Mensagem personalizada
            mensagem = (
                f"Olá {self.nome_cliente},\n\n"
                f"Seu agendamento foi **{self.status.upper()}**!\n\n"
                f"📅 **Data:** {data_horario_formatado}\n"
                f"🕒 **Horário:** {hora_formatada}\n\n"
                "Obrigado por agendar conosco! Se tiver dúvidas, entre em contato.\n"
            )

            #  Envia o e-mail
            send_mail(
                assunto,
                mensagem,
                'denisbarbeariard@gmail.com',  # 🔴 Troca pelo e-mail configurado no settings.py
                [self.email_cliente],
                fail_silently=False  # Muda pra False pra ver o erro no terminal
            )

            print("✅ E-mail enviado com sucesso!")  # Log pra debug

        except Exception as e:
            print(f"❌ Erro ao enviar e-mail: {e}")  # Log do erro


    def __str__(self):
        if self.data_horario_reserva is not None:
            data_horario_com_tz = make_aware(self.data_horario_reserva) if self.data_horario_reserva.tzinfo is None else self.data_horario_reserva
            return f"{self.nome_cliente} - {localtime(data_horario_com_tz).strftime('%d/%m/%Y %H:%M')}"
        return f"{self.nome_cliente} - (Sem data)"
