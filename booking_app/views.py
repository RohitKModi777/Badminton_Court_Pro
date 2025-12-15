import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, time

from .models import Court, Equipment, Coach, Booking, BookingSlot
from .serializers import CourtSerializer, BookingSlotSerializer, BookingSerializer
from .services.availability_service import check_court_availability
from .services.booking_service import create_booking, cancel_booking, join_waitlist
from .models import WaitlistEntry
from .services.pricing_service import PricingEngine

# --- Admin Creation View ---

def create_first_admin(request):
    """Secure admin creation using environment variables"""
    
    # Check secret key for security
    expected_secret = os.getenv('ADMIN_CREATION_SECRET')
    if not expected_secret:
        return HttpResponse('❌ ADMIN_CREATION_SECRET not configured', status=500)
    
    provided_secret = request.GET.get('secret', '')
    if provided_secret != expected_secret:
        return HttpResponse('❌ Unauthorized: Invalid secret key', status=401)
    
    User = get_user_model()
    
    # Check if admin already exists
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse(
            '❌ Admin user already exists. <br><br>'
            '<a href="/admin/">Go to Admin Panel</a>'
        )
    
    # Get credentials from environment variables
    admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('DEFAULT_ADMIN_EMAIL')
    admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
    
    # Validate required environment variables
    if not admin_email or not admin_password:
        return HttpResponse(
            '❌ DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD must be set in environment variables',
            status=500
        )
    
    try:
        # Create the superuser
        User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password
        )
        
        return HttpResponse(
            f'✅ Admin user created successfully!<br><br>'
            f'Username: <strong>{admin_username}</strong><br>'
            f'Email: <strong>{admin_email}</strong><br><br>'
            f'<a href="/admin/">Go to Admin Panel</a><br><br>'
            f'<small>Password was set from environment variables</small>'
        )
        
    except Exception as e:
        return HttpResponse(f'❌ Error creating admin: {str(e)}', status=500)

# --- Template Views ---

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful! Welcome aboard.")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def booking_wizard(request):
    # Step 1: Date Selection (in home or here)
    date_str = request.GET.get('date')
    if not date_str:
        return render(request, 'booking/select_date.html')
    
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # Generate slots for the day (9AM - 10PM)
    slots = []
    start_hour = 9
    end_hour = 22
    
    courts = Court.objects.filter(is_active=True)
    
    # Pre-fetch existing slots/bookings to optimize?
    # For simplicity, we iterate.
    
    # We want to show a grid or list of available slots.
    # Let's just show available time slots first, then pick court?
    # Or pick time + court.
    
    # Let's generate a list of time slots.
    time_slots = []
    for h in range(start_hour, end_hour):
        t = time(h, 0)
        time_slots.append(t)
        
    context = {
        'date': date_str,
        'time_slots': time_slots,
        'courts': courts,
        'equipment': Equipment.objects.all(),
        'coaches': Coach.objects.all(),
    }
    return render(request, 'booking/booking_form.html', context)

@login_required
def confirm_booking(request):
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            court_id = request.POST.get('court')
            equipment_ids = request.POST.getlist('equipment')
            coach_id = request.POST.get('coach') or None
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_str, '%H:%M').time()
            
            booking = create_booking(
                user=request.user,
                court_id=court_id,
                date_obj=date_obj,
                start_time=start_time,
                equipment_ids=equipment_ids,
                coach_id=coach_id
            )
            return redirect('booking_success', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect('home')
            
    return redirect('home')

@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking/booking_success.html', {'booking': booking})

@login_required
def dashboard(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    active_count = bookings.filter(booking_status='CONFIRMED').count()
    total_spent = sum(b.total_price for b in bookings if b.booking_status != 'CANCELLED')
    
    context = {
        'bookings': bookings,
        'active_count': active_count,
        'total_spent': total_spent,
        'waitlist': WaitlistEntry.objects.filter(user=request.user).order_by('-created_at')
    }
    return render(request, 'dashboard/my_bookings.html', context)

@login_required
def cancel_booking_view(request, booking_id):
    if request.method == 'POST':
        try:
            cancel_booking(booking_id)
            messages.success(request, "Booking cancelled successfully.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('dashboard')

@login_required
def join_waitlist_view(request):
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            time_str = request.POST.get('time')
            court_id = request.POST.get('court')
            
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(time_str, '%H:%M').time()
            
            join_waitlist(request.user, court_id, date_obj, start_time)
            messages.success(request, "Joined waitlist successfully! We'll notify you if the slot opens up.")
        except Exception as e:
            messages.error(request, str(e))
            
    return redirect('dashboard')

# --- HTMX Views ---

def calculate_price_htmx(request):
    try:
        court_id = request.GET.get('court')
        date_str = request.GET.get('date')
        time_str = request.GET.get('time')
        equipment_ids = request.GET.getlist('equipment')
        coach_id = request.GET.get('coach') or None
        
        if not (court_id and date_str and time_str):
            return HttpResponse("Select details to see price")

        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(time_str, '%H:%M').time()
        court = Court.objects.get(id=court_id)
        
        print(f"DEBUG: Checking availability for Court {court.name} ({court.id}) on {date_obj} at {start_time}")
        is_avail = check_court_availability(court.id, date_obj, start_time)
        print(f"DEBUG: Result = {is_avail}")
        
        engine = PricingEngine()
        breakdown = engine.get_price_breakdown(
            court, date_obj, start_time, equipment_ids, coach_id
        )
        
        # Use the result from above
        is_available = is_avail
        
        print(f"DEBUG: Context is_available = {is_available}")
        
        context = {
            'breakdown': breakdown,
            'is_available': is_available,
            'court_id': court_id,
            'date': date_str,
            'time': time_str
        }
        
        return render(request, 'booking/partials/price_breakdown.html', context)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

# --- API Views ---

class AvailableSlotsView(APIView):
    def get(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({"error": "Date required"}, status=400)
            
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        courts = Court.objects.filter(is_active=True)
        
        available_slots = []
        for h in range(9, 22):
            t = time(h, 0)
            for court in courts:
                if check_court_availability(court.id, date_obj, t):
                    available_slots.append({
                        'court': court.name,
                        'time': t.strftime("%H:%M"),
                        'court_id': court.id
                    })
                    
        return Response(available_slots)

class CreateBookingAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            booking = create_booking(
                user=request.user,
                court_id=request.data.get('court_id'),
                date_obj=datetime.strptime(request.data.get('date'), '%Y-%m-%d').date(),
                start_time=datetime.strptime(request.data.get('start_time'), '%H:%M').time(),
                equipment_ids=request.data.get('equipment_ids', []),
                coach_id=request.data.get('coach_id')
            )
            return Response(BookingSerializer(booking).data, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

class NotificationCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .services.notification_service import get_unread_notification_count
        count = get_unread_notification_count(request.user)
        return Response({'count': count})

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .services.notification_service import get_user_notifications
        notifications = get_user_notifications(request.user)
        
        # Check for HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'booking/partials/notification_list.html', {'notifications': notifications})
            
        data = []
        for n in notifications:
            data.append({
                'id': n.id,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at,
                'slot_id': n.slot.id if n.slot else None,
                'court_name': n.slot.court.name if n.slot else None,
                'date': n.slot.date if n.slot else None,
                'time': n.slot.start_time.strftime("%H:%M") if n.slot else None,
                'book_url': f"/api/notifications/{n.id}/book/"
            })
        return Response(data)

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        from .services.notification_service import mark_notification_as_read
        success = mark_notification_as_read(pk, request.user)
        if success:
            return Response({'status': 'success'})
        return Response({'status': 'error'}, status=404)

class NotificationBookView(View):
    def get(self, request, pk):
        from .models import WaitlistNotification
        from .services.notification_service import mark_notification_as_read
        
        try:
            notification = WaitlistNotification.objects.get(id=pk, user=request.user)
            mark_notification_as_read(pk, request.user)
            
            # Redirect to booking form with pre-filled data
            slot = notification.slot
            return redirect(f"/book/?date={slot.date}&time={slot.start_time.strftime('%H:%M')}&court={slot.court.id}")
        except WaitlistNotification.DoesNotExist:
            messages.error(request, "Notification not found or expired.")
            return redirect('dashboard')
