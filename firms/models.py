from django.db import models

# Create your models here.

class Firm(models.Model):
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True, help_text='Is the firm active?')
    flow = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name
