from django.contrib import admin

# Register your models here.
from .models import Regular_Pizza, Sicilian_Pizza, Topping, Sub, Pasta, Salad, Dinner_Platter, Category, Order, Order_Items
admin.site.register(Regular_Pizza)
admin.site.register(Sicilian_Pizza)
admin.site.register(Topping)
admin.site.register(Sub)
admin.site.register(Pasta)
admin.site.register(Salad)
admin.site.register(Dinner_Platter)
admin.site.register(Category)
admin.site.register(Order)
admin.site.register(Order_Items)