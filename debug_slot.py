import os
import django
from datetime import datetime, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "booking_system.settings")
django.setup()

from booking_app.models import BookingSlot, Court, Booking

date_obj = datetime.strptime("2025-12-16", "%Y-%m-%d").date()
start_time = time(18, 0)
court = Court.objects.get(name="Court A")

print(f"Checking slot for {court.name} on {date_obj} at {start_time}")

try:
    slot = BookingSlot.objects.get(court=court, date=date_obj, start_time=start_time)
    print(f"Slot found: ID={slot.id}, is_booked={slot.is_booked}")
    
    bookings = Booking.objects.filter(slot=slot)
    print(f"Bookings for this slot: {bookings.count()}")
    for b in bookings:
        print(f" - Booking {b.id}: Status={b.booking_status}")
        
except BookingSlot.DoesNotExist:
    print("Slot does not exist yet.")
