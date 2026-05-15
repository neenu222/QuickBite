from django.contrib import admin
from .models import (
    User, SellerProfile, CustomerProfile, FoodCategory, FoodItem, Discount, Order, OrderItem, Payment, Review, Notification, Complaint, SalesRecord
)
# Register your models here.

admin.site.register(User)
admin.site.register(SellerProfile)
admin.site.register(CustomerProfile)
admin.site.register(FoodCategory)
admin.site.register(FoodItem)
admin.site.register(Discount)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Complaint)
admin.site.register(SalesRecord)
