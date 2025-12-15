from datetime import datetime, time
from booking_app.models import PricingRule, Court, Equipment, Coach

class PricingEngine:
    def __init__(self):
        self.rule = PricingRule.objects.filter(is_active=True).first()
        if not self.rule:
            # Fallback default if no rule exists
            self.rule = PricingRule() 

    def calculate_total_price(self, court, date_obj, start_time, equipment_ids, coach_id):
        breakdown = self.get_price_breakdown(court, date_obj, start_time, equipment_ids, coach_id)
        return breakdown['total']

    def get_price_breakdown(self, court, date_obj, start_time, equipment_ids, coach_id):
        base_price = float(self.rule.base_price)
        components = {
            'base': base_price,
            'court_premium': 0.0,
            'peak_surcharge': 0.0,
            'weekend_surcharge': 0.0,
            'equipment': 0.0,
            'coach': 0.0,
            'total': 0.0
        }

        current_price = base_price

        # 1. Indoor Multiplier
        if court.court_type == 'INDOOR':
            premium = current_price * (self.rule.indoor_court_multiplier - 1)
            components['court_premium'] = round(premium, 2)
            current_price *= self.rule.indoor_court_multiplier

        # 2. Peak Hours
        # start_time is time object
        if self.rule.peak_start_time <= start_time < self.rule.peak_end_time:
            surcharge = current_price * (self.rule.peak_multiplier - 1)
            components['peak_surcharge'] = round(surcharge, 2)
            current_price *= self.rule.peak_multiplier

        # 3. Weekend
        # Monday=0, Sunday=6
        if date_obj.weekday() >= 5:
            surcharge = current_price * (self.rule.weekend_multiplier - 1)
            components['weekend_surcharge'] = round(surcharge, 2)
            current_price *= self.rule.weekend_multiplier

        # 4. Equipment
        equipment_total = 0
        if equipment_ids:
            equipment_list = Equipment.objects.filter(id__in=equipment_ids)
            for eq in equipment_list:
                equipment_total += float(eq.rent_price_per_hour)
        components['equipment'] = round(equipment_total, 2)

        # 5. Coach
        coach_total = 0
        if coach_id:
            try:
                coach = Coach.objects.get(id=coach_id)
                coach_total = float(coach.hourly_rate)
            except Coach.DoesNotExist:
                pass
        components['coach'] = round(coach_total, 2)

        # Total
        total = current_price + equipment_total + coach_total
        components['total'] = round(total, 2)
        
        return components
