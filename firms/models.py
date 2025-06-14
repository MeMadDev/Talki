from django.db import models

# Create your models here.

class Firm(models.Model):
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True, help_text='Is the firm active?')
    flow = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    first_step = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class ChatUser(models.Model):
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name='users')
    profile_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    last_message_received = models.TextField(blank=True, null=True)
    current_step = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.firm.name}"
