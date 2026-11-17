from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("inscricoes/", views.listar, name="listar"),
    path("inscricoes/nova/", views.cadastrar, name="cadastrar"),
    path(
        "inscricoes/<int:pk>/confirmar/",
        views.confirmar,
        name="confirmar",
    ),
    path(
        "inscricoes/<int:pk>/resultado/",
        views.resultado,
        name="resultado",
    ),
]