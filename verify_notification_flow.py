import os
import django
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_system.settings')
django.setup()

from django.contrib.auth.models import User
from booking_app.models import Court, BookingSlot, Booking, WaitlistEntry, WaitlistNotification
from booking_app.services.booking_service import create_booking, cancel_booking, join_waitlist

def verify_flow():
    print("Starting Verification Flow...")
    
    # Setup
    admin_user = User.objects.get(username='admin')
    test_user, _ = User.objects.get_or_create(username='testuser_verify', email='test@verify.com')
    court = Court.objects.first()
    date_obj = date(2025, 12, 30) # Future date
    start_time = time(10, 0)
    
    print(f"Test User: {test_user.username}")
    print(f"Court: {court.name}")
    
    # 1. Admin books slot
    print("\n1. Admin booking slot...")
    try:
        booking = create_booking(admin_user, court.id, date_obj, start_time, [], None)
        print(f"Booking created: {booking.id}")
    except Exception as e:
        print(f"Booking failed (might be already booked): {e}")
        # If already booked, find the booking
        slot = BookingSlot.objects.get(court=court, date=date_obj, start_time=start_time)
        booking = Booking.objects.get(slot=slot, booking_status='CONFIRMED')
        print(f"Found existing booking: {booking.id}")

    # 2. Test User joins waitlist
    print("\n2. Test User joining waitlist...")
    try:
        entry = join_waitlist(test_user, court.id, date_obj, start_time)
        print(f"Waitlist entry created: {entry.id}")
    except Exception as e:
        print(f"Join waitlist failed: {e}")
        entry = WaitlistEntry.objects.get(user=test_user, requested_slot=booking.slot)
        print(f"Found existing waitlist entry: {entry.id}")

    # 3. Admin cancels booking
    print("\n3. Admin cancelling booking...")
    cancel_booking(booking.id)
    print("Booking cancelled.")

    # 4. Verify Notification
    print("\n4. Verifying Notification...")
    notification = WaitlistNotification.objects.filter(
        user=test_user,
        slot=booking.slot,
        notification_type='SLOT_AVAILABLE'
    ).first()
    
    if notification:
        print(f"SUCCESS: Notification found! ID: {notification.id}")
        print(f"Message: {notification.message}")
        print(f"Expires at: {notification.expires_at}")
    else:
        print("FAILURE: No notification found for user.")

if __name__ == "__main__":
    verify_flow()
