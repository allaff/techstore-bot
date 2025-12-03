from django.contrib import admin
from django.urls import path
from . import views # Importa as views que criamos acima

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'), # Rota para a página
    path('api/chat/', views.chat_api, name='chat_api'), # Rota para o AJAX
]