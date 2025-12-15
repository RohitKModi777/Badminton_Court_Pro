from rest_framework import serializers
from .models import Court, Equipment, Coach, Booking, BookingSlot

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = '__all__'

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = '__all__'

class CoachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coach
        fields = '__all__'

class BookingSlotSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source='court.name', read_only=True)
    
    class Meta:
        model = BookingSlot
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source='court.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
