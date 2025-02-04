from django.db import models
from django.core.mail import send_mail
from django.utils.timezone import localtime
from django.core.exceptions import ValidationError

class Agendamento(models.Model):
    nome_cliente = models.CharField(max_length=100, help_text="Nome completo do cliente.")
    email_cliente = models.EmailField(null=True, blank=True, help_text="E-mail do cliente para comunicação.")
    data_horario_reserva = models.DateTimeField(help_text="Data e hora do agendamento.")

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('recusado', 'Recusado'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['data_horario_reserva', 'status'], name='unique_agendamento_status')
        ]
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'

    def enviar_email(self, assunto, mensagem):
        if self.email_cliente:
            try:
                send_mail(
                    assunto,
                    mensagem,
                    'denisbarbeariard@gmail.com',
                    [self.email_cliente],
                    fail_silently=True,  # Agora não quebra o sistema se der erro
                )
            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}")  # Log para o Heroku

    def clean(self):
        # Verifica se já existe um horário aceito (ignora o próprio objeto se já existir)
        if Agendamento.objects.exclude(pk=self.pk).filter(data_horario_reserva=self.data_horario_reserva, status='aceito').exists():
            raise ValidationError('Já existe uma reserva confirmada para este horário.')

    def save(self, *args, **kwargs):
        if self.pk:
            old_status = Agendamento.objects.get(pk=self.pk).status
            if old_status != self.status:
                if self.status == 'aceito':
                    self.enviar_email(
                        'Reserva confirmada',
                        f'Olá {self.nome_cliente}, sua reserva para o horário {localtime(self.data_horario_reserva).strftime("%d/%m/%Y às %H:%M")} foi confirmada!'
                    )
                elif self.status == 'recusado':
                    self.enviar_email(
                        'Reserva recusada',
                        f'Olá {self.nome_cliente}, infelizmente sua reserva para o horário {localtime(self.data_horario_reserva).strftime("%d/%m/%Y às %H:%M")} foi recusada.'
                    )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_cliente} - {localtime(self.data_horario_reserva).strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"
