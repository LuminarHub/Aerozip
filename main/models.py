from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin,BaseUserManager
from django.db.models import Max
from django.contrib.auth.hashers import make_password
# Create your models here.


class CustomUserManager(BaseUserManager):
    def create_user(self,email,name,password=None,**extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email=self.normalize_email(email)
        user=self.model(email=email,name=name,**extra_fields)
        if password:
            user.set_password(password)
        else:
            raise ValueError("Password is required")
        user.save(using=self._db)
        return user
    def create_superuser(self,email,name,password=None,**extra_fields):
        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        
        return self.create_user(email,name,password, **extra_fields)
    

class CustomUser(AbstractBaseUser,PermissionsMixin):
    name=models.CharField(max_length=200)
    email=models.EmailField(unique=True)
    phone=models.PositiveIntegerField()
    is_active=models.BooleanField(default=True)
    is_staff=models.BooleanField(default=False)
    is_superuser=models.BooleanField(default=False)
    is_company=models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name','phone']
    
    def save(self, *args, **kwargs):  
        if self.pk is None or not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        
        super().save(*args, **kwargs)


    def has_perm(self, perm, obj=None): 
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser
    
    def __str__(self):
        return self.email
    

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        """Check if OTP is still valid (within 10 minutes)"""
        import datetime
        from django.utils import timezone
        
        return (timezone.now() - self.created_at) < datetime.timedelta(minutes=10)
    
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"


from datetime import timedelta, date
import uuid

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    SHIPPING_SPEED_CHOICES = [
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
        ('overnight', 'Overnight Shipping'),
    ]
    
    SHIPMENT_TYPE_CHOICES = [
        ('international', 'International'),
        ('domestic', 'Domestic'),
    ]

    tracking_number = models.CharField(max_length=50, unique=True,editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    sender_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='sender_address', null=True)
    recipient_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='receiver_address')

    # New Fields for Airport Selection
    shipment_type = models.CharField(max_length=20, choices=SHIPMENT_TYPE_CHOICES, default='domestic')
    from_airport_name = models.CharField(max_length=500, null=True, blank=True)
    from_airport_place = models.CharField(max_length=500, null=True, blank=True)
    from_airport_code = models.CharField(max_length=500, null=True, blank=True)
    to_airport_name = models.CharField(max_length=500, null=True, blank=True)
    to_airport_place = models.CharField(max_length=500, null=True, blank=True)
    to_airport_code = models.CharField(max_length=500, null=True, blank=True)

    weight = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_speed = models.CharField(max_length=20, choices=SHIPPING_SPEED_CHOICES, default='standard')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    cancellation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    def generate_tracking_number(self):
        """Generate a unique tracking number (e.g., SHIP-ABC12345)"""
        while True:
            tracking_id = f"SHIP-{uuid.uuid4().hex[:8].upper()}"  # Example: SHIP-AB12CD34
            if not Shipment.objects.filter(tracking_number=tracking_id).exists():
                return tracking_id
    
    def calculate_estimated_delivery(self):
        """Automatically set estimated delivery date based on shipment type and speed."""
        base_days = 3 if self.shipment_type == "domestic" else 5  # Domestic: 3 days, International: 5 days
        max_days = 7 if self.shipment_type == "domestic" else 14  # Domestic: 7 days, International: 14 days

        if self.shipping_speed == "express":
            delivery_days = base_days + 1
        elif self.shipping_speed == "overnight":
            delivery_days = base_days  # Overnight = fastest
        else:
            delivery_days = (base_days + max_days) // 2  # Average for standard

        return date.today() + timedelta(days=delivery_days)

    def calculate_shipping_cost(self):
        """Automatically calculate shipping cost based on type, weight, and speed."""
        base_cost = 500 if self.shipment_type == "domestic" else 1000
        weight_cost = 100 if self.shipment_type == "domestic" else 300
        total_cost = base_cost + (self.weight * weight_cost)

        if self.shipping_speed == "express":
            total_cost *= 1.2  # 20% increase
        elif self.shipping_speed == "overnight":
            total_cost *= 1.5  # 50% increase

        return round(total_cost, 2)

    def calculate_status(self):
        """Determine shipment status based on estimated delivery and current date."""
        if self.is_paid:
            days_passed = (date.today() - self.created_at.date()).days

            if days_passed < 1:
                return 'pending'
            elif days_passed < 2:
                return 'processing'
            elif days_passed < (self.estimated_delivery - timedelta(days=2)).day:
                return 'in_transit'
            elif days_passed < (self.estimated_delivery - timedelta(days=1)).day:
                return 'out_for_delivery'
            else:
                return 'delivered'
        return self.status  # Default if no estimated delivery set

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        if not self.estimated_delivery:
            self.estimated_delivery = self.calculate_estimated_delivery()
        if not self.shipping_cost:
            self.shipping_cost = self.calculate_shipping_cost()
        
        self.status = self.calculate_status()  # Automatically update status
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shipment {self.tracking_number} ({self.status})"



class ShipmentTrackingUpdate(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='tracking_updates')
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=200)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.status}"
    
    
class InternationalAirports(models.Model):
    name = models.CharField(max_length=500)
    code = models.CharField(max_length=100,unique=True)
    location = models.CharField(max_length=500)
    
    def __str__(self):
        return self.name
    
    
class DomesticAirports(models.Model):
    name = models.CharField(max_length=500)
    code = models.CharField(max_length=100,unique=True)
    location = models.CharField(max_length=500)
    
    def __str__(self):
        return self.name
    
    
class TrackingSearchHistory(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True)
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name='tracking_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.shipment.tracking_number}  at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"



class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    shipment = models.ForeignKey('Shipment', on_delete=models.CASCADE, related_name='payments')
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.order_id} for {self.shipment.tracking_number}"

class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    shipment = models.ForeignKey('Shipment', on_delete=models.CASCADE, related_name='receipts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receipt {self.id} for {self.shipment.tracking_number}"



class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews')
    shipment_id = models.CharField(max_length=20, blank=True, null=True)
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=100)
    comment = models.TextField()
    delivery_satisfaction = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username}'s Review - {self.rating} stars"




