from django.contrib import admin
from .models import *

admin.site.register(Product)
admin.site.register(Orders)
admin.site.register(OrderItem)
admin.site.register(ProductCategory)
admin.site.register(UserProfile)
admin.site.register(OrderHistory)
# Register your models here.
