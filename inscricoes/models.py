from django.db import models


class Inscricao(models.Model):
    class Modalidade(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        DUPLA = "dupla", "Dupla"

    class StatusPagamento(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        CONFIRMADO = "confirmado", "Confirmado"

    modalidade = models.CharField(
        max_length=10,
        choices=Modalidade.choices,
    )
    status_pagamento = models.CharField(
        max_length=10,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    confirmada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    modalidade__in=["individual", "dupla"]
                ),
                name="inscricao_modalidade_valida",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status_pagamento="pendente",
                        confirmada_em__isnull=True,
                    )
                    | models.Q(
                        status_pagamento="confirmado",
                        confirmada_em__isnull=False,
                    )
                ),
                name="inscricao_pagamento_coerente",
            ),
        ]

    def __str__(self):
        return f"Inscrição {self.pk} — {self.get_modalidade_display()}"


class Integrante(models.Model):
    inscricao = models.ForeignKey(
        Inscricao,
        on_delete=models.CASCADE,
        related_name="integrantes",
    )
    nome = models.CharField(max_length=150)
    posicao = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["posicao"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscricao", "posicao"],
                name="integrante_posicao_unica",
            ),
            models.CheckConstraint(
                condition=models.Q(posicao__in=[1, 2]),
                name="integrante_posicao_valida",
            ),
        ]

    def __str__(self):
        return self.nome