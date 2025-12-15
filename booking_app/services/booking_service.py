from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from booking_app.models import Booking, Court, Equipment, Coach, BookingSlot, WaitlistEntry
from booking_app.services.pricing_service import PricingEngine
from booking_app.services.availability_service import check_court_availability, check_coach_availability
from booking_app.services.notification_service import create_slot_available_notification

@transaction.atomic
def create_booking(user, court_id, date_obj, start_time, equipment_ids, coach_id):
    # 1. Lock Court
    # Ensure court exists and is active
    try:
        court = Court.objects.select_for_update().get(id=court_id, is_active=True)
    except Court.DoesNotExist:
        raise ValidationError("Court not found or inactive.")

    # 2. Check/Create Slot and Lock it
    # We need to ensure no one else is booking this specific slot right now.
    # If we just check Booking table, there might be a race condition.
    # So we use BookingSlot as the lock target.
    slot, created = BookingSlot.objects.get_or_create(
        court=court,
        date=date_obj,
        start_time=start_time,
        defaults={'end_time': start_time.replace(hour=start_time.hour + 1)} # Assuming 1 hour
    )
    
    # Lock the slot
    slot = BookingSlot.objects.select_for_update().get(id=slot.id)
    
    if slot.is_booked:
        raise ValidationError("Slot already booked.")

    # 3. Check Coach Availability
    if coach_id:
        if not check_coach_availability(coach_id, date_obj, start_time):
             raise ValidationError("Coach not available.")
        # Optional: Lock coach if needed, but availability check might be enough if we don't have a strict slot model for coaches.
        # For strictness:
        # coach = Coach.objects.select_for_update().get(id=coach_id)

    # 4. Check and Lock Equipment
    # The prompt explicitly asked for this logic:
    equipment_list = []
    if equipment_ids:
        # Filter and lock
        equipment_list = list(Equipment.objects.select_for_update().filter(
            id__in=equipment_ids,
            quantity_available__gte=1
        ))
        
        if len(equipment_list) != len(set(equipment_ids)):
            raise ValidationError("Some equipment is not available.")

        # Update quantities atomically (as per prompt requirement)
        # Note: In a real production app, we'd handle inventory differently (time-based).
        for eq in equipment_list:
            eq.quantity_available = F('quantity_available') - 1
            eq.save()

    # 5. Calculate Price
    pricing_engine = PricingEngine()
    total_price = pricing_engine.calculate_total_price(
        court, date_obj, start_time, equipment_ids, coach_id
    )

    # 6. Create Booking
    booking = Booking.objects.create(
        user=user,
        court=court,
        coach_id=coach_id,
        slot=slot,
        total_price=total_price,
        booking_status='CONFIRMED'
    )
    
    if equipment_list:
        booking.equipment.set(equipment_list)

    # 7. Mark slot as booked
    slot.is_booked = True
    slot.save()

    return booking

@transaction.atomic
def cancel_booking(booking_id):
    try:
        booking = Booking.objects.select_for_update().get(id=booking_id)
    except Booking.DoesNotExist:
        raise ValidationError("Booking not found.")

    if booking.booking_status == 'CANCELLED':
        return booking

    # Restore equipment quantity
    for eq in booking.equipment.all():
        # Lock equipment to increment safely
        eq_locked = Equipment.objects.select_for_update().get(id=eq.id)
        eq_locked.quantity_available = F('quantity_available') + 1
        eq_locked.save()

    # Free up the slot
    slot = booking.slot
    slot = BookingSlot.objects.select_for_update().get(id=slot.id)
    slot.is_booked = False
    slot.save()

    booking.booking_status = 'CANCELLED'
    booking.save()
    
    # Check Waitlist
    next_waitlist = WaitlistEntry.objects.filter(
        requested_slot=slot, 
        notified=False
    ).order_by('created_at').first()
    
    if next_waitlist:
        # Create notification for the user
        create_slot_available_notification(next_waitlist.user, slot)
    
    return booking

def join_waitlist(user, court_id, date_obj, start_time):
    court = Court.objects.get(id=court_id)
    slot, created = BookingSlot.objects.get_or_create(
        court=court,
        date=date_obj,
        start_time=start_time,
        defaults={'end_time': start_time.replace(hour=start_time.hour + 1)}
    )
    
    if not slot.is_booked:
        raise ValidationError("Slot is available, you can book it directly.")
        
    # Check if already in waitlist
    if WaitlistEntry.objects.filter(user=user, requested_slot=slot).exists():
        raise ValidationError("You are already on the waitlist for this slot.")
        
    position = WaitlistEntry.objects.filter(requested_slot=slot).count() + 1
    
    entry = WaitlistEntry.objects.create(
        user=user,
        requested_slot=slot,
        court=court,
        position=position
    )
    return entry
