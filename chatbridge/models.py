from django.db import models

# Create your models here.

class MessageLog(models.Model):
    DIRECTION_CHOICES = [
        ('IN', 'Incoming'),
        ('OUT', 'Outgoing'),
    ]
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, blank=True)
    # New fields for WhatsApp message details
    whatsapp_business_account_id = models.CharField(max_length=64, blank=True)
    firm_phone_number = models.CharField(max_length=20, blank=True)
    user_name = models.CharField(max_length=255, blank=True)
    message_id = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f"{self.direction} - {self.phone_number} - {self.timestamp}"
