from datetime import datetime, time
from django.db.models import Q
from booking_app.models import BookingSlot, Booking, Equipment, Coach

def check_court_availability(court_id, date_obj, start_time):
    """
    Check if a court is available at a specific date and time.
    """
    # Check if slot exists and is not booked
    try:
        slot = BookingSlot.objects.get(
            court_id=court_id,
            date=date_obj,
            start_time=start_time
        )
        if slot.is_booked:
            return False
    except BookingSlot.DoesNotExist:
        # If slot doesn't exist, it's technically available to be created/booked
        # But we should probably ensure slots are pre-generated or generated on demand.
        # For this logic, let's assume if it's not explicitly booked in BookingSlot, it's free?
        # No, the requirement says "Show available time slots".
        # So we should probably rely on BookingSlot being the source of truth for availability.
        # If slot doesn't exist, we can treat it as available if within operating hours.
        pass

    # Double check against actual Bookings to be safe (though slot.is_booked should handle it)
    is_booked = Booking.objects.filter(
        court_id=court_id,
        slot__date=date_obj,
        slot__start_time=start_time,
        booking_status='CONFIRMED'
    ).exists()
    
    return not is_booked

def check_equipment_availability(equipment_ids, date_obj, start_time, duration_hours=1):
    """
    Check if requested equipment is available.
    Note: This is a simple check. For strict concurrency, we use select_for_update in booking_service.
    """
    # In a real system, we'd need to sum up all bookings using this equipment at this time.
    # Since equipment quantity is global, we subtract currently active bookings' usage.
    
    # This is tricky without a time-based inventory system.
    # The requirement says: "Equipment: quantity_available".
    # And "Update quantities atomically" in booking_service.
    # This implies quantity_available is a global counter.
    # BUT, if I rent a racket for 9-10AM, it should be available again at 10AM.
    # If we just decrement `quantity_available` on booking, we need to increment it back when booking ends.
    # Or, `quantity_available` represents TOTAL stock, and we calculate *current* availability dynamically.
    
    # Given the "Atomic Booking System" requirement:
    # "Update quantities atomically... eq.quantity_available = F('quantity_available') - 1"
    # This strongly suggests the user wants a simple decrement approach.
    # However, that would permanently deplete stock.
    # I will implement the dynamic check here for display purposes, 
    # but the booking service will likely need to handle the temporary lock or we assume the prompt 
    # implies a simpler "decrement for the session" model which might be flawed but requested.
    
    # WAIT. "quantity_available" in Equipment model usually means "Total owned by the facility".
    # If we decrement it, we lose track of total.
    # Let's assume the prompt's `quantity_available` means "Currently on shelf".
    # So when a booking starts, we decrement. When it ends, we increment.
    # But for *future* bookings, we can't just check current value.
    
    # CORRECT APPROACH for "Check availability":
    # Count total items - items booked at that specific slot.
    
    unavailable_counts = {}
    for eq_id in equipment_ids:
        # Count confirmed bookings using this equipment at this time
        booked_count = Booking.objects.filter(
            slot__date=date_obj,
            slot__start_time=start_time,
            booking_status='CONFIRMED',
            equipment__id=eq_id
        ).count()
        
        equipment = Equipment.objects.get(id=eq_id)
        if booked_count >= equipment.quantity_available:
             return False
             
    return True

def check_coach_availability(coach_id, date_obj, start_time):
    """
    Check if coach is available.
    """
    if not coach_id:
        return True
        
    # Check if coach is already booked
    is_booked = Booking.objects.filter(
        coach_id=coach_id,
        slot__date=date_obj,
        slot__start_time=start_time,
        booking_status='CONFIRMED'
    ).exists()
    
    if is_booked:
        return False
        
    # Check coach's schedule (availability_slots)
    # availability_slots = {"Mon": ["09:00", "10:00"], ...}
    coach = Coach.objects.get(id=coach_id)
    day_name = date_obj.strftime("%a") # Mon, Tue...
    
    available_slots = coach.availability_slots.get(day_name, [])
    # start_time is datetime.time, convert to string "HH:MM"
    time_str = start_time.strftime("%H:%M")
    
    # If the coach has specific slots listed, check if time is in them.
    # If list is empty or key missing, maybe assume unavailable? Or available?
    # Let's assume explicit allow-list.
    if time_str not in available_slots:
        return False
        
    return True
