from django.db import models

class ClienteFila(models.Model):
    nome_ou_mensagem = models.CharField(max_length=255)
    data_entrada = models.DateTimeField(auto_now_add=True)
    atendido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nome_ou_mensagem} - {self.data_entrada}"