from django.contrib import admin
from .models import Court, Equipment, Coach, PricingRule, BookingSlot, Booking, WaitlistEntry

@admin.action(description='Mark selected courts as active')
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description='Mark selected courts as inactive')
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'court_type', 'is_active')
    list_filter = ('court_type', 'is_active')
    actions = [make_active, make_inactive]

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'equipment_type', 'quantity_available', 'rent_price_per_hour')
    list_editable = ('quantity_available', 'rent_price_per_hour')
    list_filter = ('equipment_type',)

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('name', 'hourly_rate')

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'peak_multiplier', 'weekend_multiplier', 'is_active')
    list_editable = ('is_active', 'base_price')

@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    list_display = ('court', 'date', 'start_time', 'is_booked')
    list_filter = ('date', 'court', 'is_booked')

class BookingInline(admin.TabularInline):
    model = Booking.equipment.through
    extra = 0

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'court', 'slot', 'total_price', 'booking_status', 'created_at')
    list_filter = ('booking_status', 'court', 'created_at')
    search_fields = ('user__username', 'id')
    readonly_fields = ('total_price', 'created_at')
    exclude = ('equipment',) # Exclude M2M field to use inline if needed, but M2M is hard to inline directly without through model.
    # Actually, standard M2M widget is fine.

@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'court', 'requested_slot', 'position', 'notified')
