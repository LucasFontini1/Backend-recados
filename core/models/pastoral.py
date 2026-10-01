from django.db import models

from uploader.models import Image


class Pastoral(models.Model):
    name = models.CharField(max_length=100)
    image = models.ForeignKey(Image, on_delete=models.CASCADE, null=True, blank=True)
    color = models.CharField(max_length=7, default='#06402b')  # default color is a shade of green

    def __str__(self):
        return f'{self.name} - {self.color}'
