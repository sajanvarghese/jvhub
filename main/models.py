from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator



class SuperUserManager(BaseUserManager):
    def create_user(self, gst_number, password=None):
        if not gst_number:
            raise ValueError("GST Number is required")

        user = self.model(
            gst_number=gst_number,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, gst_number, password=None):
        user = self.create_user(
            gst_number=gst_number,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class SuperUser(AbstractBaseUser, PermissionsMixin):
    gst_number = models.CharField(max_length=15, unique=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = SuperUserManager()

    USERNAME_FIELD = "gst_number"   # login with GST
    REQUIRED_FIELDS = []            # only password required

    def __str__(self):
        return self.gst_number


# -------------------------
# Normal registered users
# -------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    gst_number = models.CharField(max_length=15, unique=True)
    pincode = models.CharField(max_length=6)
    address = models.TextField()
    password = models.CharField(max_length=128, default="")
    location = models.CharField(max_length=100, blank=True, null=True)
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name
    
# product table

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    MRP = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.PositiveIntegerField(blank=True, null=True)
    unit = models.CharField(max_length=50, default="pcs")
    min_amount = models.PositiveIntegerField(
    default=0,
    validators=[MinValueValidator(0)])
    Quantity = models.CharField(max_length=50, default="kg")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="product_images/", blank=True, null=True)

    def __str__(self):
        return self.name
    
class Route(models.Model):
    DAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    day = models.CharField(max_length=20, choices=DAYS)
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.location} - {self.day}"

#----------orders
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateField(null=True, blank=True) 

    @property
    def total_amount(self):
        return self.quantity * self.product.price
from django.utils import timezone

class Notification(models.Model):
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    type = models.CharField(
        max_length=20,
        choices=[("customer", "Customer"), ("order", "Order")],
    )


    def __str__(self):
        return self.message
class CustomerNotification(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_notifications")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.customer.username} - {self.message}"

