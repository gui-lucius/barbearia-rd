from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Agendamento
from dateutil import parser  # Import necessário para parsear datas com fuso horário
from django.shortcuts import render

# Endpoint para criar agendamentos
@api_view(['POST'])
def criar_agendamento(request):
    try:
        dados = request.data  # Correto para pegar os dados do JSON enviado

        nome_cliente = dados.get('nome_cliente')
        email_cliente = dados.get('email_cliente')
        data_horario_reserva = dados.get('data_horario_reserva')

        # Validações básicas
        if not nome_cliente or not email_cliente or not data_horario_reserva:
            return JsonResponse({'erro': 'Todos os campos são obrigatórios.'}, status=400)

        try:
            validate_email(email_cliente)
        except ValidationError:
            return JsonResponse({'erro': 'E-mail inválido.'}, status=400)

        try:
            # Usando dateutil.parser para lidar com diferentes formatos de data
            data_horario_reserva = parser.parse(data_horario_reserva)
        except ValueError:
            return JsonResponse({'erro': 'Data/Horário inválido.'}, status=400)

        # Criando o agendamento
        agendamento = Agendamento.objects.create(
            nome_cliente=nome_cliente,
            email_cliente=email_cliente,
            data_horario_reserva=data_horario_reserva,
            status='pendente'
        )

        # Tentativa de envio de e-mail (não quebra o código se falhar)
        try:
            send_mail(
                'Novo Agendamento Pendente',
                f"Você tem uma nova solicitação de agendamento de {nome_cliente} no horário {data_horario_reserva}. "
                "Por favor, verifique o painel administrativo.",
                'denisbarbeariard@gmail.com',
                ['denisbarbeariard@gmail.com'],
                fail_silently=False,  # Se der erro, não interrompe a aplicação
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")  # Log para debug

        return JsonResponse({'mensagem': 'Agendamento criado com sucesso!', 'id': agendamento.id}, status=201)
    
    except Exception as e:
        print(f"Erro ao criar agendamento: {e}")  # Log para debug
        return JsonResponse({'erro': f'Erro inesperado: {str(e)}'}, status=500)

# Endpoint para listar horários ocupados e pendentes
@api_view(['GET'])
def horarios_ocupados(request):
    try:
        horarios = Agendamento.objects.all().values('data_horario_reserva', 'status')
        return Response(list(horarios))  # Agora retorna o status também
    except Exception as e:
        print(f"Erro ao buscar horários ocupados: {e}")
        return Response({'erro': f'Erro inesperado: {str(e)}'}, status=500)


# Página inicial
def home(request):
    return render(request, 'index.html')
