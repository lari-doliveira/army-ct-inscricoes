from django.test import TestCase


from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .forms import InscricaoForm
from .models import Inscricao, Integrante


class ValidacaoFormularioTests(SimpleTestCase):
    def test_individual_valido(self):
        form = InscricaoForm({
            "modalidade": "individual",
            "primeiro_integrante": "Alfa",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_dupla_exige_segundo_integrante(self):
        form = InscricaoForm({
            "modalidade": "dupla",
            "primeiro_integrante": "Beta",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("segundo_integrante", form.errors)

    def test_individual_rejeita_segundo_integrante(self):
        form = InscricaoForm({
            "modalidade": "individual",
            "primeiro_integrante": "Alfa",
            "segundo_integrante": "Beta",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("segundo_integrante", form.errors)

    def test_rejeita_nome_vazio_html_e_modalidade_invalida(self):
        casos = [
            {"primeiro_integrante": "   "},
            {"primeiro_integrante": "<script>alert(1)</script>"},
            {"modalidade": "trio"},
        ]
        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                dados = {
                    "modalidade": "individual",
                    "primeiro_integrante": "Alfa",
                }
                dados.update(alteracao)
                self.assertFalse(InscricaoForm(dados).is_valid())


class FluxoInscricoesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser(
            username="operador_teste",
            password="SenhaFicticiaSomenteParaTeste!2026",
        )
        self.client.force_login(self.usuario)

    def cadastrar(self, modalidade, primeiro, segundo=""):
        return self.client.post(reverse("cadastrar"), {
            "modalidade": modalidade,
            "primeiro_integrante": primeiro,
            "segundo_integrante": segundo,
        })

    def test_cadastro_confirmacao_e_contagem_da_dupla(self):
        resposta = self.cadastrar("individual", "Alfa")
        self.assertRedirects(resposta, reverse("listar"))

        self.cadastrar("dupla", "Beta", "Gama")
        self.assertEqual(Inscricao.objects.count(), 2)
        self.assertEqual(Integrante.objects.count(), 3)

        resposta = self.client.get(reverse("listar"))
        self.assertEqual(resposta.context["total_confirmado"], 0)

        for inscricao in Inscricao.objects.all():
            resposta = self.client.post(
                reverse("confirmar", args=[inscricao.pk])
            )
            self.assertEqual(resposta.status_code, 302)

        resposta = self.client.get(reverse("listar"))
        self.assertEqual(resposta.context["total_confirmado"], 2)
        self.assertContains(resposta, "Beta")
        self.assertContains(resposta, "Gama")

    def test_confirmacao_repetida_preserva_data_e_total(self):
        self.cadastrar("dupla", "Beta", "Gama")
        inscricao = Inscricao.objects.get()
        url = reverse("confirmar", args=[inscricao.pk])

        self.client.post(url)
        inscricao.refresh_from_db()
        primeira_data = inscricao.confirmada_em
        self.assertIsNotNone(primeira_data)

        self.client.post(url)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.confirmada_em, primeira_data)
        self.assertEqual(Inscricao.objects.count(), 1)

        resposta = self.client.get(reverse("listar"))
        self.assertEqual(resposta.context["total_confirmado"], 1)

    def test_cadastro_invalido_nao_grava_registros(self):
        resposta = self.cadastrar("dupla", "Beta")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Inscricao.objects.count(), 0)
        self.assertEqual(Integrante.objects.count(), 0)

    def test_transacao_desfaz_inscricao_se_integrante_falhar(self):
        form = InscricaoForm({
            "modalidade": "individual",
            "primeiro_integrante": "Alfa",
        })
        self.assertTrue(form.is_valid())

        with patch(
            "inscricoes.forms.Integrante.objects.create",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                form.save()

        self.assertEqual(Inscricao.objects.count(), 0)
        self.assertEqual(Integrante.objects.count(), 0)

    def test_visitante_nao_pode_cadastrar(self):
        self.client.logout()
        resposta = self.cadastrar("individual", "Alfa")
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("login")))
        self.assertEqual(Inscricao.objects.count(), 0)

    def test_usuario_sem_permissao_nao_pode_confirmar(self):
        self.cadastrar("individual", "Alfa")
        inscricao = Inscricao.objects.get()
        usuario = get_user_model().objects.create_user(
            username="sem_permissao",
            password="SenhaFicticiaTeste!2026",
        )
        self.client.force_login(usuario)

        resposta = self.client.post(
            reverse("confirmar", args=[inscricao.pk])
        )
        self.assertEqual(resposta.status_code, 403)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status_pagamento, "pendente")

    def test_get_nao_confirma_pagamento(self):
        self.cadastrar("individual", "Alfa")
        inscricao = Inscricao.objects.get()

        resposta = self.client.get(
            reverse("confirmar", args=[inscricao.pk])
        )
        self.assertEqual(resposta.status_code, 200)
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status_pagamento, "pendente")

    def test_post_sem_csrf_e_bloqueado(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)

        resposta = cliente.post(reverse("cadastrar"), {
            "modalidade": "individual",
            "primeiro_integrante": "Alfa",
        })
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Inscricao.objects.count(), 0)