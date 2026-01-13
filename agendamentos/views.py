# agendamentos/views.py

from datetime import timedelta

from dateutil import parser
from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Agendamento, HorarioBloqueado


def home(request):
    return render(request, "index.html")


def calendario(request):
    return render(request, "calendario.html")


def _parse_datetime(dt_str: str):
    """
    Faz parse da string e normaliza timezone:
    - Se vier timezone-aware -> converte pra localtime (ou mantém)
    - Se vier naive -> mantém naive (compatível com USE_TZ=False)
    """
    dt = parser.parse(dt_str)

    # Se o projeto estiver usando TZ, garante aware
    if getattr(settings, "USE_TZ", False):
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        else:
            dt = timezone.localtime(dt)
    return dt


@api_view(["POST"])
def criar_agendamento(request):
    dados = request.data

    nome_cliente = (dados.get("nome_cliente") or "").strip()
    email_cliente = (dados.get("email_cliente") or "").strip()
    data_horario_reserva_str = dados.get("data_horario_reserva")

    if not nome_cliente or not email_cliente or not data_horario_reserva_str:
        return Response({"erro": "Todos os campos são obrigatórios."}, status=400)

    try:
        validate_email(email_cliente)
    except ValidationError:
        return Response({"erro": "E-mail inválido."}, status=400)

    try:
        data_horario_reserva = _parse_datetime(data_horario_reserva_str)
    except Exception:
        return Response({"erro": "Data/Horário inválido."}, status=400)

    # ✅ Checa horário bloqueado antes de criar
    if HorarioBloqueado.objects.filter(data_horario=data_horario_reserva).exists():
        return Response({"erro": "Esse horário está bloqueado. Escolha outro."}, status=409)

    # ✅ Criação segura: transação + tratamento de conflito do UniqueConstraint
    try:
        with transaction.atomic():
            agendamento = Agendamento.objects.create(
                nome_cliente=nome_cliente,
                email_cliente=email_cliente,
                data_horario_reserva=data_horario_reserva,
                status="pendente",
            )
    except IntegrityError:
        return Response({"erro": "Esse horário já foi reservado. Escolha outro."}, status=409)

    # E-mail pro dono (pode deixar assim por enquanto)
    try:
        send_mail(
            "Novo Agendamento Pendente",
            (
                f"Nova solicitação de agendamento:\n\n"
                f"Cliente: {nome_cliente}\n"
                f"E-mail: {email_cliente}\n"
                f"Horário: {data_horario_reserva}\n\n"
                "Verifique o painel administrativo."
            ),
            "denisbarbeariard@gmail.com",
            ["denisbarbeariard@gmail.com"],
            fail_silently=True,  # em DEV evita quebrar a API por SMTP
        )
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

    return Response({"mensagem": "Agendamento criado com sucesso!", "id": agendamento.id}, status=201)


@api_view(["GET"])
def horarios_ocupados(request):
    # Retorna horários que devem aparecer como ocupados no calendário
    horarios = Agendamento.objects.filter(status__in=["pendente", "aceito"]).values(
        "data_horario_reserva", "status"
    )
    return Response(list(horarios))


@api_view(["GET"])
def horarios_bloqueados(request):
    bloqueios = HorarioBloqueado.objects.all().values("data_horario")
    return Response(list(bloqueios))


@api_view(["GET"])
def eventos_calendario(request):
    """
    Se tu quiser alimentar um FullCalendar com eventos já prontos.
    (Tu ainda não tinha essa rota no urls.py; eu deixo pronta.)
    """
    agendamentos = Agendamento.objects.filter(status__in=["pendente", "aceito"])
    bloqueios = HorarioBloqueado.objects.all()

    eventos = []
    for ag in agendamentos:
        dt = ag.data_horario_reserva
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(dt):
            dt = timezone.localtime(dt)

        eventos.append(
            {
                "title": f"Agendado: {ag.nome_cliente}",
                "start": dt.isoformat(),
                "allDay": False,
            }
        )

    for b in bloqueios:
        dt = b.data_horario
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(dt):
            dt = timezone.localtime(dt)

        eventos.append(
            {
                "title": "🔴 BLOQUEADO",
                "start": dt.isoformat(),
                "end": (dt + timedelta(minutes=30)).isoformat(),  # ajuste conforme tua duração real
                "allDay": False,
            }
        )

    return Response(eventos)
