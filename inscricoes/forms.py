from django import forms
from django.db import transaction

from .models import Inscricao, Integrante


class InscricaoForm(forms.Form):
    modalidade = forms.ChoiceField(
        label="Modalidade",
        choices=Inscricao.Modalidade.choices,
    )
    primeiro_integrante = forms.CharField(
        label="Primeiro integrante",
        max_length=150,
    )
    segundo_integrante = forms.CharField(
        label="Segundo integrante",
        max_length=150,
        required=False,
        help_text="Obrigatório apenas para inscrições em dupla.",
    )

    def clean(self):
        dados = super().clean()

        for campo in ("primeiro_integrante", "segundo_integrante"):
            nome = dados.get(campo, "").strip()
            dados[campo] = nome

            if "<" in nome or ">" in nome:
                self.add_error(
                    campo,
                    "Informe somente o nome, sem marcações HTML.",
                )

        modalidade = dados.get("modalidade")
        segundo = dados.get("segundo_integrante", "")

        if modalidade == Inscricao.Modalidade.DUPLA and not segundo:
            self.add_error(
                "segundo_integrante",
                "Informe o nome do segundo integrante da dupla.",
            )

        if modalidade == Inscricao.Modalidade.INDIVIDUAL and segundo:
            self.add_error(
                "segundo_integrante",
                "Uma inscrição individual deve ter apenas um integrante.",
            )

        return dados

    @transaction.atomic
    def save(self):
        if not self.is_valid():
            raise ValueError("Não é possível salvar um formulário inválido.")

        inscricao = Inscricao.objects.create(
            modalidade=self.cleaned_data["modalidade"],
        )

        Integrante.objects.create(
            inscricao=inscricao,
            nome=self.cleaned_data["primeiro_integrante"],
            posicao=1,
        )

        if inscricao.modalidade == Inscricao.Modalidade.DUPLA:
            Integrante.objects.create(
                inscricao=inscricao,
                nome=self.cleaned_data["segundo_integrante"],
                posicao=2,
            )

        return inscricao