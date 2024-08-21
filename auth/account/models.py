from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.contrib.auth.models import PermissionsMixin
 
class UserManager(BaseUserManager):
    def create_user(self, phone, email, password=None, is_staff=False, is_active=True, is_admin=False):
        if not phone:
            raise ValueError('users must have a phone number')
        if not password:
            raise ValueError('user must have a password')
        if not email:
            raise ValueError('user must have email')

        email = self.normalize_email(email)

        user_obj = self.model(
            phone=phone,
            email = email
        )
        user_obj.set_password(password)
        user_obj.staff = is_staff
        user_obj.active = is_active
        user_obj.admin = is_admin
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self, phone, email, password=None):
        user = self.create_user(
            phone,
            email,
            password=password,
            is_staff=True,
        )
        return user

    def create_superuser(self, phone, email, password=None):
        user = self.create_user(
            phone,
            email,
            password=password,
            is_staff=True,
            is_admin=True,
        )
        return user

phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

class User(AbstractBaseUser,PermissionsMixin):
    # abstract base user or abstract user
    phone = models.CharField(validators=[phone_regex], max_length=15, unique=True)
    email = models.EmailField(unique=True,max_length=100)
    name = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)
    # need pillow to install for imagefield
    image = models.ImageField(upload_to="images/", blank=True, null=True)
    ip = models.CharField(max_length=10, blank=True, null=True)

    active = models.BooleanField(default=False)
    staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin = models.BooleanField(default=False)

    otp = models.CharField(null=True,blank=True,max_length=6)
    otp_expiry = models.DateTimeField(blank=True,null=True)
    max_otp_try = models.CharField(max_length=2,default=3)
    otp_max_out =  models.DateTimeField(blank=True,null=True)
    # Prevent directly calling the send_otp, verify otp endpoint
    otp_pending =  models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    def __str__(self):
        return self.phone

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.phone

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.staff

    @property
    def is_active(self):
        return self.active

    @property
    def is_admin(self):
        return self.admin
