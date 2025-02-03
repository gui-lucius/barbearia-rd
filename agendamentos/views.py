from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Agendamento
from datetime import datetime
import json
from django.shortcuts import render

# Endpoint para criar agendamentos
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_agendamento(request):
    try:
        dados = json.loads(request.body)
        nome_cliente = dados.get('nome_cliente')
        email_cliente = dados.get('email_cliente')
        data_horario_reserva = dados.get('data_horario_reserva')

        # Validações
        if not nome_cliente or not email_cliente or not data_horario_reserva:
            return JsonResponse({'erro': 'Todos os campos são obrigatórios.'}, status=400)

        try:
            validate_email(email_cliente)
        except ValidationError:
            return JsonResponse({'erro': 'E-mail inválido.'}, status=400)

        try:
            datetime.strptime(data_horario_reserva, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return JsonResponse({'erro': 'Data/Horário inválido.'}, status=400)

        # Criação do agendamento
        agendamento = Agendamento.objects.create(
            nome_cliente=nome_cliente,
            email_cliente=email_cliente,
            data_horario_reserva=data_horario_reserva,
            status='pendente'
        )

        # Envio de e-mail
        send_mail(
            'Novo Agendamento Pendente',
            f"Você tem uma nova solicitação de agendamento de {nome_cliente} no horário {data_horario_reserva}. "
            "Por favor, verifique o painel administrativo.",
            'denisbarbeariard@gmail.com',
            ['denisbarbeariard@gmail.com'],
            fail_silently=False,
        )

        return JsonResponse({'mensagem': 'Agendamento criado com sucesso!', 'id': agendamento.id}, status=201)
    except Exception:
        return JsonResponse({'erro': 'Erro inesperado. Tente novamente mais tarde.'}, status=500)


# Endpoint para listar horários ocupados
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def horarios_ocupados(request):
    try:
        horarios = Agendamento.objects.filter(status='aceito').values('data_horario_reserva')
        return Response(list(horarios))
    except Exception:
        return Response({'erro': 'Erro inesperado. Tente novamente mais tarde.'}, status=500)

def home (request):
    return render(request, 'index.html')