from datetime import date
from django.db import transaction
from outflows.models import Outflow
from .models import Signature


def generate_signature_outflows():
    """
    Checks all active signatures and generates Outflow records for the current month 
    if they haven't been generated yet.
    """
    today = date.today()
    active_signatures = Signature.objects.filter(is_active=True)
    
    for signature in active_signatures:
        # Check if we need to generate for this month/year
        needs_generation = False
        
        if signature.last_generated_year is None or signature.last_generated_month is None:
            needs_generation = True
        elif today.year > signature.last_generated_year:
            needs_generation = True
        elif today.year == signature.last_generated_year and today.month > signature.last_generated_month:
            needs_generation = True
            
        if needs_generation:
            # We only generate if the billing day has arrived or passed
            # Handle months with fewer days (e.g., February)
            import calendar
            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            effective_billing_day = min(signature.billing_day, last_day_of_month)
            
            if today.day >= effective_billing_day:
                with transaction.atomic():
                    # Create the Outflow
                    Outflow.objects.create(
                        title=f"Assinatura: {signature.name}",
                        bank=signature.bank,
                        category=signature.category,
                        value=signature.value
                    )
                    
                    # Update signature tracking
                    signature.last_generated_month = today.month
                    signature.last_generated_year = today.year
                    signature.save()
