from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Court(models.Model):
    COURT_TYPES = [
        ('INDOOR', 'Indoor'),
        ('OUTDOOR', 'Outdoor'),
    ]
    name = models.CharField(max_length=100)
    court_type = models.CharField(max_length=10, choices=COURT_TYPES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_court_type_display()})"

class Equipment(models.Model):
    EQUIPMENT_TYPES = [
        ('RACKET', 'Racket'),
        ('SHOES', 'Shoes'),
    ]
    name = models.CharField(max_length=100)
    equipment_type = models.CharField(max_length=10, choices=EQUIPMENT_TYPES)
    quantity_available = models.PositiveIntegerField(default=0)
    rent_price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

class Coach(models.Model):
    name = models.CharField(max_length=100)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    # Store availability as JSON: {"Mon": ["09:00", "10:00"], ...} or simplified
    availability_slots = models.JSONField(default=dict) 

    def __str__(self):
        return self.name

class PricingRule(models.Model):
    name = models.CharField(max_length=100, default="Standard Rule")
    peak_start_time = models.TimeField(default="18:00")
    peak_end_time = models.TimeField(default="21:00")
    peak_multiplier = models.FloatField(default=1.5)
    weekend_multiplier = models.FloatField(default=1.3)
    indoor_court_multiplier = models.FloatField(default=1.4)
    base_price = models.DecimalField(max_digits=6, decimal_places=2, default=500.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class BookingSlot(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('court', 'date', 'start_time')

    def __str__(self):
        return f"{self.court.name} - {self.date} {self.start_time}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    coach = models.ForeignKey(Coach, on_delete=models.SET_NULL, null=True, blank=True)
    equipment = models.ManyToManyField(Equipment, blank=True)
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.user.username}"

class WaitlistNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('SLOT_AVAILABLE', 'Slot Available'),
        ('POSITION_CHANGED', 'Position Changed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"

class UserNotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Prefs for {self.user.username}"

class WaitlistEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_slot = models.ForeignKey(BookingSlot, on_delete=models.CASCADE)
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    notified = models.BooleanField(default=False)
    notification = models.ForeignKey(WaitlistNotification, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waitlist {self.user.username} - {self.requested_slot}"
