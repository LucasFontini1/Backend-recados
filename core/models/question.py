from django.conf import settings
from django.db import models

class Question(models.Model):
    subject = models.CharField(max_length=150)
    text = models.TextField(max_length=5000)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='questions')
    created_at = models.DateTimeField(auto_now_add=True)
    answer = models.TextField(max_length=5000, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='answered_questions',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pergunta à diretoria'
        verbose_name_plural = 'Perguntas à diretoria'

    def __str__(self):
        return self.subject
