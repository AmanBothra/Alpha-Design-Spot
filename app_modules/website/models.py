from django.db import models

from lib.models import BaseModel


class Enquiry(BaseModel):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    standard = models.CharField(max_length=30)
    message =  models.TextField()
    
    def __str__(self) -> str:
        return self.phone_number
    
    
class Testimonial(BaseModel):
    image = models.FileField(upload_to="website/testimonal/")
    client_name = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        return self.client_name
