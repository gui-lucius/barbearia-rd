# agendamentos/views.py

from datetime import timedelta
import logging

from dateutil import parser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Agendamento, HorarioBloqueado
from .email_service import send_resend_email, get_barbeiro_email


logger = logging.getLogger(__name__)


def home(request):
    return render(request, "index.html")


def calendario(request):
    return render(request, "calendario.html")


def _parse_datetime(dt_str: str):
    """
    Faz parse da string e normaliza timezone:
    - Se USE_TZ=True: garante aware e converte pra timezone local
    - Se USE_TZ=False: mantém naive (compatível com teu settings atual)
    """
    dt = parser.parse(dt_str)

    if getattr(settings, "USE_TZ", False):
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        else:
            dt = timezone.localtime(dt)

    return dt


def _send_agendamento_email(nome_cliente: str, email_cliente: str, data_horario_reserva):
    """
    Envia email pro BARBEIRO/ADMIN avisando que tem agendamento pendente.
    Agora via RESEND (API), evitando SMTP no Railway.
    """
    destino = (get_barbeiro_email() or "").strip()
    if not destino:
        logger.warning("BARBEARIA_EMAIL vazio: email de notificação não será enviado.")
        return

    subject = "Novo Agendamento Pendente"

    # Texto simples (backup)
    text = (
        "Nova solicitação de agendamento:\n\n"
        f"Cliente: {nome_cliente}\n"
        f"E-mail: {email_cliente}\n"
        f"Horário: {data_horario_reserva}\n\n"
        "Verifique o painel administrativo."
    )

    # HTML (bonitinho e legível no email)
    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.4;">
      <h2>Novo Agendamento Pendente</h2>
      <p><strong>Cliente:</strong> {nome_cliente}</p>
      <p><strong>E-mail:</strong> {email_cliente}</p>
      <p><strong>Horário:</strong> {data_horario_reserva}</p>
      <hr/>
      <p>Verifique o painel administrativo para aceitar ou recusar.</p>
    </div>
    """

    try:
        send_resend_email(
            to_email=destino,
            subject=subject,
            html=html,
            text=text,
        )
        logger.info("Email de agendamento enviado com sucesso (Resend) para %s.", destino)
    except Exception:
        # já tem logger.exception no email_service, mas mantém aqui também
        logger.exception("Erro ao enviar email de agendamento (Resend).")


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

    # Bloqueio manual
    if HorarioBloqueado.objects.filter(data_horario=data_horario_reserva).exists():
        return Response({"erro": "Esse horário está bloqueado. Escolha outro."}, status=409)

    try:
        with transaction.atomic():
            agendamento = Agendamento.objects.create(
                nome_cliente=nome_cliente,
                email_cliente=email_cliente,
                data_horario_reserva=data_horario_reserva,
                status="pendente",
            )

            _send_agendamento_email(nome_cliente, email_cliente, data_horario_reserva)

    except IntegrityError:
        return Response({"erro": "Esse horário já foi reservado. Escolha outro."}, status=409)

    # Resposta completa (ajuda o front a atualizar sem refresh)
    dt = agendamento.data_horario_reserva
    if getattr(settings, "USE_TZ", False) and timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return Response(
        {
            "mensagem": "Agendamento criado com sucesso!",
            "id": agendamento.id,
            "status": agendamento.status,
            "data_horario_reserva": dt.isoformat(),
        },
        status=201,
    )


@api_view(["GET"])
def horarios_ocupados(request):
    ags = Agendamento.objects.filter(status__in=["pendente", "aceito"]).values(
        "data_horario_reserva",
        "status",
    )

    resultado = []
    for item in ags:
        dt = item["data_horario_reserva"]
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(dt):
            dt = timezone.localtime(dt)

        resultado.append(
            {
                "data_horario_reserva": dt.isoformat() if hasattr(dt, "isoformat") else dt,
                "status": item["status"],
            }
        )

    return Response(resultado)


@api_view(["GET"])
def horarios_bloqueados(request):
    bloqueios = HorarioBloqueado.objects.all().values("data_horario")

    resultado = []
    for item in bloqueios:
        dt = item["data_horario"]
        if getattr(settings, "USE_TZ", False) and timezone.is_aware(dt):
            dt = timezone.localtime(dt)

        resultado.append({"data_horario": dt.isoformat() if hasattr(dt, "isoformat") else dt})

    return Response(resultado)


@api_view(["GET"])
def eventos_calendario(request):
    """
    Opcional: alimentar um FullCalendar com eventos prontos.
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
                "end": (dt + timedelta(minutes=30)).isoformat(),
                "allDay": False,
            }
        )

    return Response(eventos)