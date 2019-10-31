from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(NstAdminEmail)
admin.site.register(NstLocation)
admin.site.register(NstMetropolisMajor)
admin.site.register(NstNeighborhood)
admin.site.register(NstCombinedRegion)
admin.site.register(NstAltName)
admin.site.register(NstParkSystem)
# memcache status page here b/c this is the heaviest use
admin.site.index_template = "memcache_status/admin_index.html"
