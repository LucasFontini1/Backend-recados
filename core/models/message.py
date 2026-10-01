import uuid

from django.db import models

from uploader.models import Image

from .Category import Category
from .pastoral import Pastoral
from .user import User


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    text = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='messages')
    event_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pastoral = models.ForeignKey(Pastoral, on_delete=models.CASCADE, related_name='messages')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='messages')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.autor.name} - {self.created_at}'
