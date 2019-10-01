from django.db import models
from django.contrib.auth.models import User


class FitnessPlan(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    premium = models.BooleanField(default=True)

# whenever someone wants a Premium Subcription, we have to make a customer account for them. This is different than the user object


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripeid = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    cancel_at_period_end = models.BooleanField(default=False)
    membership = models.BooleanField(default=False)
