from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Agendamento
from dateutil import parser  # Import necessário para parsear datas com fuso horário
from django.shortcuts import render
from .models import HorarioBloqueado


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

@api_view(['GET'])
def horarios_ocupados(request):
    try:
        # Agora filtra apenas os horários "pendente" e "aceito"
        horarios = Agendamento.objects.filter(status__in=['pendente', 'aceito']).values('data_horario_reserva', 'status')
        return Response(list(horarios))  # Retorna os horários sem os recusados
    except Exception as e:
        print(f"Erro ao buscar horários ocupados: {e}")
        return Response({'erro': f'Erro inesperado: {str(e)}'}, status=500)

# Página inicial
def home(request):
    return render(request, 'index.html')

from .models import HorarioBloqueado

def get_agendamentos(request):
    agendamentos = Agendamento.objects.filter(disponivel=True)
    bloqueios = HorarioBloqueado.objects.all()  # Busca os horários bloqueados

    eventos = [
        {
            "title": f"Agendado: {ag.nome_cliente}" if ag.nome_cliente else "Disponível",
            "start": ag.data_horario_reserva.isoformat(),
            "clickable": ag.disponivel,  # Só permite clique se estiver disponível
            "backgroundColor": "#28a745" if ag.disponivel else "#dc3545",  # Verde = disponível, vermelho = bloqueado
            "borderColor": "#28a745" if ag.disponivel else "#dc3545",
        }
        for ag in agendamentos
    ]

    # Adiciona os bloqueios ao calendário
    eventos += [
        {
            "title": "Indisponível",
            "start": bloqueio.data_horario.isoformat(),
            "clickable": False,  # Cliente não pode clicar
            "backgroundColor": "#000000",  # Preto para bloqueios
            "borderColor": "#000000",
        }
        for bloqueio in bloqueios
    ]

    return JsonResponse(eventos, safe=False)
