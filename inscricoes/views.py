from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import InscricaoForm
from .models import Inscricao


@never_cache
@login_required
@permission_required("inscricoes.view_inscricao", raise_exception=True)
@require_http_methods(["GET"])
def inicio(request):
    return render(request, "inscricoes/inicio.html")


@never_cache
@login_required
@permission_required("inscricoes.add_inscricao", raise_exception=True)
@require_http_methods(["GET", "POST"])
def cadastrar(request):
    form = InscricaoForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        inscricao = form.save()
        messages.success(
            request,
            f"Inscrição {inscricao.pk} cadastrada como pendente.",
        )
        return redirect("listar")

    return render(request, "inscricoes/cadastrar.html", {"form": form})


@never_cache
@login_required
@permission_required("inscricoes.view_inscricao", raise_exception=True)
@require_http_methods(["GET"])
def listar(request):
    status = request.GET.get("status", "")

    status_validos = {
        Inscricao.StatusPagamento.PENDENTE,
        Inscricao.StatusPagamento.CONFIRMADO,
    }

    if status not in status_validos:
        status = ""

    inscricoes = Inscricao.objects.prefetch_related("integrantes")

    if status:
        inscricoes = inscricoes.filter(status_pagamento=status)

    total_confirmado = Inscricao.objects.filter(
        status_pagamento=Inscricao.StatusPagamento.CONFIRMADO
    ).count()

    return render(
        request,
        "inscricoes/listar.html",
        {
            "inscricoes": inscricoes,
            "total_confirmado": total_confirmado,
            "status_selecionado": status,
        },
    )


@never_cache
@login_required
@permission_required("inscricoes.change_inscricao", raise_exception=True)
@require_http_methods(["GET", "POST"])
def confirmar(request, pk):
    inscricao = get_object_or_404(
        Inscricao.objects.prefetch_related("integrantes"),
        pk=pk,
    )

    if request.method == "POST":
        atualizadas = Inscricao.objects.filter(
            pk=pk,
            status_pagamento=Inscricao.StatusPagamento.PENDENTE,
        ).update(
            status_pagamento=Inscricao.StatusPagamento.CONFIRMADO,
            confirmada_em=timezone.now(),
        )

        if atualizadas:
            messages.success(request, "Pagamento confirmado.")
        else:
            messages.info(request, "Este pagamento já estava confirmado.")

        return redirect("resultado", pk=pk)

    return render(
        request,
        "inscricoes/confirmar.html",
        {"inscricao": inscricao},
    )


@never_cache
@login_required
@permission_required("inscricoes.view_inscricao", raise_exception=True)
@require_http_methods(["GET"])
def resultado(request, pk):
    inscricao = get_object_or_404(
        Inscricao.objects.prefetch_related("integrantes"),
        pk=pk,
    )
    total_confirmado = Inscricao.objects.filter(
        status_pagamento=Inscricao.StatusPagamento.CONFIRMADO
    ).count()

    return render(
        request,
        "inscricoes/resultado.html",
        {
            "inscricao": inscricao,
            "total_confirmado": total_confirmado,
        },
    )