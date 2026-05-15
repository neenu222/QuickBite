from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone



# -------------------------------------
# 1. CUSTOM USER MODEL
# -------------------------------------

class User(AbstractUser):
    USER_TYPES = (
        ('admin', 'Admin'),
        ('seller', 'Seller'),
        ('customer', 'Customer'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPES)

    def __str__(self):
        return f"{self.username} ({self.user_type})"


# -------------------------------------
# 2. SELLER PROFILE
# -------------------------------------

class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=200)
    shop_address = models.TextField()
    phone = models.CharField(max_length=15)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.shop_name


# -------------------------------------
# 3. CUSTOMER PROFILE
# -------------------------------------

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    def __str__(self):
        return self.user.username




# -------------------------------------
# 4. FOOD CATEGORY
# -------------------------------------

class FoodCategory(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -------------------------------------
# 5. FOOD ITEM
# -------------------------------------

class FoodItem(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(FoodCategory, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    price = models.FloatField()
    description = models.TextField()
    image = models.ImageField(upload_to="food_items/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    discount_percent = models.PositiveIntegerField(default=0)

    def discounted_price(self):
        if self.discount_percent > 0:
            discount_amount = (self.price * self.discount_percent) / 100
            return self.price - discount_amount
        return self.price

    def __str__(self):
        return self.name


# -------------------------------------
# 6. DISCOUNT / COUPON
# -------------------------------------

class Discount(models.Model):
    code = models.CharField(max_length=50, unique=True)
    percentage = models.IntegerField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


# -------------------------------------
# 7. ORDER
# -------------------------------------

class Order(models.Model):
    STATUS = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('delivered', 'Delivered'),
    )

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    total_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.user.username}"


# -------------------------------------
# 8. ORDER ITEMS
# -------------------------------------

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.FloatField()

    def __str__(self):
        return f"{self.food_item.name} x {self.quantity}"


# -------------------------------------
# 9. PAYMENT
# -------------------------------------

# class Payment(models.Model):
    # PAYMENT_STATUS = (
    #     ('pending', 'Pending'),
    #     ('success', 'Success'),
    #     ('failed', 'Failed'),
    # )

    # order = models.OneToOneField(Order, on_delete=models.CASCADE)
    # amount = models.FloatField()
    # status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    # payment_date = models.DateTimeField(auto_now_add=True)
    # transaction_id = models.CharField(max_length=200, null=True, blank=True)

    # def __str__(self):
    #     return f"Payment for Order {self.order.id}"

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")],
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)



# -------------------------------------
# 10. REVIEW / RATING
# -------------------------------------

class Review(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating} Stars by {self.customer.user.username}"



# Complaint
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_complaints')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)

    subject = models.CharField(max_length=200)
    message = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reply = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.customer.username}"


# review
class Review(models.Model):
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='customer_reviews'
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seller_reviews'
    )

    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Review by {self.customer.username} for {self.seller.username}"




# -------------------------------------
# 11. NOTIFICATION
# -------------------------------------

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


# -------------------------------------
# 12. COMPLAINT / FEEDBACK
# -------------------------------------

class Complaint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reply = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Complaint by {self.user.username}"


# -------------------------------------
# 13. ANALYTICS SUPPORT MODEL
# -------------------------------------

class SalesRecord(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    total_sales = models.FloatField()
    total_orders = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Analytics {self.seller.shop_name}"
