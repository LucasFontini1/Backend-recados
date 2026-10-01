from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#06402b')  # default color is a shade of green

    def __str__(self):
        return f'{self.name} - {self.color}'