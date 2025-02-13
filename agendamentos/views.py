from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Agendamento, HorarioBloqueado
from dateutil import parser 
from django.shortcuts import render
from datetime import timedelta

def home(request):
    return render(request, 'index.html')

@api_view(['POST'])
def criar_agendamento(request):
    try:
        dados = request.data

        nome_cliente = dados.get('nome_cliente')
        email_cliente = dados.get('email_cliente')
        data_horario_reserva = dados.get('data_horario_reserva')

        if not nome_cliente or not email_cliente or not data_horario_reserva:
            return JsonResponse({'erro': 'Todos os campos são obrigatórios.'}, status=400)

        try:
            validate_email(email_cliente)
        except ValidationError:
            return JsonResponse({'erro': 'E-mail inválido.'}, status=400)

        try:
            data_horario_reserva = parser.parse(data_horario_reserva)
        except ValueError:
            return JsonResponse({'erro': 'Data/Horário inválido.'}, status=400)

        agendamento = Agendamento.objects.create(
            nome_cliente=nome_cliente,
            email_cliente=email_cliente,
            data_horario_reserva=data_horario_reserva,
            status='pendente'
        )

        try:
            send_mail(
                'Novo Agendamento Pendente',
                f"Você tem uma nova solicitação de agendamento de {nome_cliente} no horário {data_horario_reserva}. "
                "Por favor, verifique o painel administrativo.",
                'denisbarbeariard@gmail.com',
                ['denisbarbeariard@gmail.com'],
                fail_silently=False,  
            )
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")

        return JsonResponse({'mensagem': 'Agendamento criado com sucesso!', 'id': agendamento.id}, status=201)
    
    except Exception as e:
        print(f"Erro ao criar agendamento: {e}") 
        return JsonResponse({'erro': f'Erro inesperado: {str(e)}'}, status=500)

@api_view(['GET'])
def horarios_ocupados(request):
    try:
        horarios = Agendamento.objects.filter(status__in=['pendente', 'aceito']).values(
            'data_horario_reserva', 'status'
        )
        return Response(list(horarios))  
    except Exception as e:
        print(f"Erro ao buscar horários ocupados: {e}")
        return Response({'erro': f'Erro inesperado: {str(e)}'}, status=500)
    
@api_view(['GET'])
def horarios_bloqueados(request):
    try:
        bloqueios = HorarioBloqueado.objects.all().values('data_horario')
        return Response(list(bloqueios))
    except Exception as e:
        print(f"Erro ao buscar horários bloqueados: {e}")
        return Response({'erro': f'Erro inesperado: {str(e)}'}, status=500)

def get_agendamentos(request):
    agendamentos = Agendamento.objects.filter(disponivel=True)
    bloqueios = HorarioBloqueado.objects.all() 

    eventos = [
        {
            "title": f"Agendado: {ag.nome_cliente}" if ag.nome_cliente else "Disponível",
            "start": ag.data_horario_reserva.isoformat(),
            "clickable": ag.disponivel, 
            "backgroundColor": "#28a745" if ag.disponivel else "#dc3545",
            "borderColor": "#28a745" if ag.disponivel else "#dc3545",
        }
        for ag in agendamentos
    ]

    eventos += [
        {
            "title": "🔴 BLOQUEADO",
            "start": bloqueio.data_horario.isoformat(),
            "end": (bloqueio.data_horario + timedelta(minutes=1)).isoformat(),
            "clickable": False,  
            "backgroundColor": "#000000",
            "borderColor": "#000000",
        }
        for bloqueio in bloqueios
    ]

    return JsonResponse(eventos, safe=False)
