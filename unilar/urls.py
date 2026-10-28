from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='home'),
    path('inicio/', views.inicio, name='inicio'),
    path('catalogo/<slug:slug>/favoritar/', views.favoritar_catalogo, name='favoritar_catalogo'),
    path('login/', views.login, name='login'),
    path('imoveis/', views.imoveis, name='imoveis'),
    path('imoveis/kitnet-no-centro/', views.detalhe_imovel, name='detalhe_imovel'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('imoveis/kitnet-no-centro/favoritar/', views.favoritar_imovel, name='favoritar_imovel'),
    path('imoveis/kitnet-no-centro/contato/', views.contato_imovel, name='contato_imovel'),
    path('imoveis/kitnet-no-centro/visita/', views.solicitar_visita, name='solicitar_visita'),
]
