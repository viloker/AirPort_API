from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from phonenumber_field.modelfields import PhoneNumberField

from user.manager import UserManager

class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    number_phone = PhoneNumberField(unique=True, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["email", "password"]

    objects = UserManager()

    def __str__(self):
        return self.email