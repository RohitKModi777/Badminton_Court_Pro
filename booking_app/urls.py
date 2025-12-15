from django.urls import path
from . import views

urlpatterns = [
    # Template Views
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('book/', views.booking_wizard, name='booking_wizard'),
    path('book/confirm/', views.confirm_booking, name='confirm_booking'),
    path('book/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('waitlist/join/', views.join_waitlist_view, name='join_waitlist'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    
    # HTMX
    path('htmx/calculate-price/', views.calculate_price_htmx, name='calculate_price_htmx'),
    
    # API
    path('api/available-slots/', views.AvailableSlotsView.as_view(), name='api_available_slots'),
    path('api/create-booking/', views.CreateBookingAPI.as_view(), name='api_create_booking'),
    
    # Notifications
    path('api/notifications/count/', views.NotificationCountView.as_view(), name='notification_count'),
    path('api/notifications/list/', views.NotificationListView.as_view(), name='notification_list'),
    path('api/notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('api/notifications/<int:pk>/book/', views.NotificationBookView.as_view(), name='notification_book'),
]
