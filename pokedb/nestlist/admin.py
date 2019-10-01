from django.contrib import admin

# Register your models here.
from .models import (
    NstLocation,
    NstCombinedRegion,
    NstParkSystem,
    NstNeighborhood,
    NstMetropolisMajor,
)

admin.site.register(NstLocation)
