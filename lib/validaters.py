from django.core.validators import RegexValidator
from django.utils import timezone

from rest_framework.exceptions import ValidationError

PHONE_REGEX = RegexValidator(
    regex=r'^\d{7,12}$',
    message="Phone number should be between 9 to 12 digits."
)


def no_past_date(value):
    today = timezone.now().date()
    if value < today:
        raise ValidationError('Date cannot be in the past.')
    

def validate_dates(start_date, end_date):
    if start_date and end_date and end_date < start_date:
        return False
    return True
