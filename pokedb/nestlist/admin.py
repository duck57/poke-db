from django.contrib import admin

# Register your models here.
from .models import Pokemon, NstLocation, Type

admin.site.register(NstLocation)
