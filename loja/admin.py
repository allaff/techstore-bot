from django.contrib import admin
from .models import ClienteFila

# Configuração para mostrar colunas bonitas no painel
class ClienteFilaAdmin(admin.ModelAdmin):
    list_display = ('nome_ou_mensagem', 'data_entrada', 'atendido')
    list_filter = ('atendido', 'data_entrada')
    search_fields = ('nome_ou_mensagem',)

admin.site.register(ClienteFila, ClienteFilaAdmin)