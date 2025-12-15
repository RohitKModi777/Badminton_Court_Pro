from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from ..models import WaitlistNotification, WaitlistEntry, BookingSlot

def create_slot_available_notification(user, slot):
    """
    Creates a notification for a user when a slot becomes available.
    Sets expiration to 15 minutes from creation.
    """
    expires_at = timezone.now() + timedelta(minutes=15)
    
    notification = WaitlistNotification.objects.create(
        user=user,
        slot=slot,
        notification_type='SLOT_AVAILABLE',
        message=f"Good news! The slot for {slot.court.name} on {slot.date} at {slot.start_time} is now available.",
        expires_at=expires_at
    )
    
    # Update WaitlistEntry to link notification
    try:
        entry = WaitlistEntry.objects.get(user=user, requested_slot=slot)
        entry.notification = notification
        entry.notified = True
        entry.save()
    except WaitlistEntry.DoesNotExist:
        pass
        
    return notification

def mark_notification_as_read(notification_id, user):
    """
    Marks a notification as read.
    """
    try:
        notification = WaitlistNotification.objects.get(id=notification_id, user=user)
        notification.is_read = True
        notification.save()
        return True
    except WaitlistNotification.DoesNotExist:
        return False

def get_unread_notification_count(user):
    """
    Returns the count of unread, non-expired notifications for a user.
    """
    cleanup_expired_notifications() # Lazy cleanup
    return WaitlistNotification.objects.filter(
        user=user, 
        is_read=False,
        expires_at__gt=timezone.now()
    ).count()

def get_user_notifications(user):
    """
    Returns all valid notifications for a user, ordered by creation time.
    """
    cleanup_expired_notifications() # Lazy cleanup
    return WaitlistNotification.objects.filter(
        user=user,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')

def cleanup_expired_notifications():
    """
    Marks notifications as expired or handles expiration logic.
    For now, we just filter them out in getters, but we could delete them or mark as expired.
    Also, if a notification expires, we should notify the NEXT person on the waitlist.
    """
    expired_notifications = WaitlistNotification.objects.filter(
        expires_at__lte=timezone.now(),
        is_read=False # Only act if not read/acted upon? 
        # Actually, if they read it but didn't book, it still expires.
        # But for "notifying next person", we need to know if it was booked.
    )
    
    # Logic to notify next person is complex to do here without a scheduled task.
    # For this MVP, we will just hide expired notifications.
    # The "notify next person" logic would ideally be a periodic task.
    pass
