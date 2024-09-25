from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, name, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, name, password, **extra_fields)


class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    
    name = models.CharField(max_length=150)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True, db_index=True)
    email = models.EmailField(blank=True, null=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['name']
    
    username = None
    
    objects = CustomUserManager()

    def __str__(self):
        return self.name + self.phone_number

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=17)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return self.name + self.phone_number

class SpamReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spam_reports')
    phone_number = models.CharField(max_length=17)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # we can add the spam_count in the user table and inc or count when same got added (for more efficient we can use the redis or kafka to update the count if count>=1000 by that we avoid calling db frequently)
    class Meta:
        unique_together = ('reporter', 'phone_number')
    
    def __str__(self):
        return self.phone_number+ self.reporter.name
        