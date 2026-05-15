
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from .models import User, CustomerProfile, SellerProfile
from .models import FoodCategory, FoodItem, Order, OrderItem, Payment, Review, Notification, Complaint, SalesRecord, Discount
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import CustomerProfile, Order
from django.db.models import Sum



def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


# CUSTOMER REGISTRATION
def register_customer(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        profile_photo = request.FILES.get("profile_photo")

        #  Validate required fields
        if not username or not email or not password or not confirm_password:
            messages.error(
                request, "Username, Email, Password and Confirm Password are required.")
            return redirect("register_customer")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register_customer")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register_customer")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register_customer")

        #  Create User safely
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type="customer",
            is_active=True  # you can set False if you want email verification
        )

        # Create CustomerProfile
        CustomerProfile.objects.create(
            user=user,
            phone=phone,
            address=address,
            profile_photo=profile_photo
        )

        messages.success(
            request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "auth/register_customer.html")


# SELLER REGISTRATION
def register_seller(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        phone = request.POST.get("phone", "").strip()
        shop_name = request.POST.get("shop_name", "").strip()
        shop_address = request.POST.get("shop_address", "").strip()

        #  Validate required fields
        if not username or not email or not password or not confirm_password or not shop_name:
            messages.error(
                request, "Username, Email, Password, Confirm Password and Shop Name are required.")
            return redirect("register_seller")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("register_seller")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register_seller")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register_seller")

        #  Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type="seller",
            is_active=True
        )

        # Create SellerProfile
        SellerProfile.objects.create(
            user=user,
            phone=phone,
            shop_name=shop_name,
            shop_address=shop_address,
            is_approved=False # Admin approval pending
        )

        messages.success(request, "Seller account created! Waiting for admin approval.")
        return redirect("login")

    return render(request, "auth/register_seller.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return redirect("login")

        user = authenticate(username=username, password=password)
        if user is None:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

        if not user.is_active:
            messages.error(request, "Your account is disabled.")
            return redirect("login")

        # 🔐 ADMIN (highest priority)
        if user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")

        # 🔐 SELLER
        if user.user_type == "seller":
            seller = SellerProfile.objects.get(user=user)
            if not seller.is_approved:
                logout(request)
                messages.error(
                    request, "Seller account pending admin approval.")
                return redirect("login")

            login(request, user)
            return redirect("seller_dashboard")

        # 🔐 CUSTOMER
        if user.user_type == "customer":
            login(request, user)
            return redirect("customer_home")

        messages.error(request, "User role not recognized.")
        return redirect("login")

    return render(request, "auth/login.html")


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect("login")


# CUSTOMER HOME


@login_required
def customer_home(request):
    categories = FoodCategory.objects.all()
    food_items = FoodItem.objects.filter(is_available=True)

    query = request.GET.get('q')  # get search keyword
    category_id = request.GET.get('category')

    if query:
        food_items = food_items.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(seller__shop_name__icontains=query)
        )

    activate_category = None
    if category_id:
        activate_category = get_object_or_404(FoodCategory, id=category_id)
        food_items = food_items.filter(category=activate_category)

    return render(request, 'customer/customer_home.html', {
        'categories': categories,
        'food_items': food_items,
        'query': query,
        'activate_category': activate_category
    })


@login_required
def food_detail(request, item_id):
    food = get_object_or_404(FoodItem, id=item_id, is_available=True)

    return render(request, 'customer/food_details.html', {
        'food': food
    })


@login_required
def add_to_cart(request, item_id):
    food = FoodItem.objects.get(id=item_id, is_available=True)

    cart = request.session.get('cart', {})

    item_id_str = str(item_id)

    original_price = float(food.price)
    discounted_price = float(food.discounted_price())
    discount_percent = food.discount_percent or 0

    

    if item_id_str in cart:
        cart[item_id_str]['quantity'] += 1
    else:
        cart[item_id_str] = {
            'food_id': food.id,
            'seller_id': food.seller.id,
            'name': food.name,
            'price': discounted_price,
            'original_price': original_price,   # For UI
            'discount_percent': discount_percent,
            'quantity': 1
        }

    request.session['cart'] = cart
    messages.success(request, f"{food.name} added to cart")

    return redirect('cart')


@login_required
def cart_view(request):
    cart = request.session.get('cart', {})

    total = 0

    for item in cart.values():
        item['subtotal'] = item['price'] * item['quantity']
        total += item['subtotal']

    return render(request, 'customer/cart.html', {
        'cart': cart,
        'total': total
    })


@login_required
def remove_from_cart(request, item_id):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        del cart[item_id_str]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart")

    return redirect('cart')

@login_required
def increase_cart_quantity(request, item_id):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        cart[item_id_str]['quantity'] += 1
        request.session.modified = True

    return redirect('cart')

@login_required
def decrease_cart_item(request, item_id):
    cart = request.session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        cart[item_id_str]['quantity'] -= 1

        # If quantity becomes 0 → remove item completely
        if cart[item_id_str]['quantity'] <= 0:
            del cart[item_id_str]

    request.session['cart'] = cart
    return redirect('cart')



@login_required
def customer_orders(request):
    if request.user.user_type != "customer":
        return redirect("login")

    customer = CustomerProfile.objects.get(user=request.user)

    orders = Order.objects.filter(customer=customer).order_by("-created_at")

    return render(request, "customer/customer_orders.html", {
        "orders": orders
    })

# ORDER SUCCESS PAGE


def order_success(request):
    return render(request, "customer/order_success.html")


# profile view


@login_required
def customer_profile(request):
    if request.user.user_type != "customer":
        return redirect("login")

    customer = CustomerProfile.objects.get(user=request.user)

    return render(request, "customer/customer_profile.html", {
        "customer": customer
    })


@login_required
def edit_customer_profile(request):
    if request.user.user_type != "customer":
        return redirect("login")

    user = request.user
    customer = CustomerProfile.objects.get(user=user)

    if request.method == "POST":
        # Update User table
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()

        # ✅ Update CustomerProfile table
        customer.phone = request.POST.get("phone", "")
        customer.address = request.POST.get("address", "")

        # ✅ Update profile photo (only if uploaded)
        if request.FILES.get("profile_photo"):
            customer.profile_photo = request.FILES.get("profile_photo")

        customer.save()

        messages.success(request, "Profile updated successfully")
        return redirect("customer_profile")

    return render(request, "customer/edit_profile.html", {
        "customer": customer
    })


# approve seller action
# @login_required
# def approve_seller(request, seller_id):
#     seller = get_object_or_404(SellerProfile, id=seller_id)
#     seller.is_approved = True
#     seller.save()
#     messages.success(request, "Seller approved successfully")
#     return redirect("admin_seller_approval")


@login_required
def admin_seller_approval(request):
    sellers = SellerProfile.objects.filter(is_approved=False)
    return render(request, "adminpanel/seller_approval.html", {"sellers": sellers})


# admin - manage-seller


# admin view customer


@login_required
@admin_required
def admin_customers(request):
    customers = CustomerProfile.objects.all()
    return render(request, "adminpanel/admin_customer.html", {"customers": customers})

# admin view order


@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by("-created_at")
    return render(request, "adminpanel/admin_orders.html", {"orders": orders})

# admin view complaint


@admin_required
def admin_complaints(request):
    complaints = Complaint.objects.all().order_by("-created_at")
    return render(request, "adminpanel/admin_complaints.html", {"complaints": complaints})

# admin food category


@admin_required
def admin_categories(request):
    categories = FoodCategory.objects.all().order_by("-created_at")
    return render(request, "adminpanel/admin_categories.html", {"categories": categories})


@admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name is required")
            return redirect("admin_categories")

        if FoodCategory.objects.filter(name__iexact=name).exists():
            messages.error(request, "Category already exists")
            return redirect("admin_categories")

        FoodCategory.objects.create(name=name)
        messages.success(request, "Category added successfully")
        return redirect("admin_categories")

    return redirect("admin_categories")


@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(FoodCategory, id=category_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name cannot be empty")
            return redirect("admin_categories")

        category.name = name
        category.save()
        messages.success(request, "Category updated successfully")
        return redirect("admin_categories")

    return redirect("admin_categories")


@admin_required
def delete_category(request, category_id):
    category = get_object_or_404(FoodCategory, id=category_id)

    # Safety check: prevent delete if foods exist
    if FoodItem.objects.filter(category=category).exists():
        messages.error(
            request,
            "Cannot delete category. Food items are linked to it."
        )
        return redirect("admin_categories")

    category.delete()
    messages.success(request, "Category deleted successfully")
    return redirect("admin_categories")

# seller module


def seller_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != "seller":
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@seller_required
def seller_dashboard(request):
    seller = SellerProfile.objects.get(user=request.user)
    orders = Order.objects.filter(seller=seller)
    total_foods = FoodItem.objects.filter(seller=seller).count()
    total_orders = orders.count()
    pending_orders = orders.filter(status="PENDING").count()

    total_sales = orders.filter(
        status="DELIVERED"
    ).aggregate(total=Sum("total_amount"))["total"] or 0


    # context = {
    #     "total_orders": orders.count(),
    #     "pending_orders": orders.filter(status="pending").count(),
    #     "delivered_orders": orders.filter(status="delivered").count(),
    # }
    context = {
        "total_foods": FoodItem.objects.filter(seller=seller).count(),
        "total_orders": orders.count(),
        "pending_orders": orders.filter(status="PENDING").count(),
        "total_sales": total_sales,
    }
    return render(request, "seller/seller_dashboard.html", context)


@login_required
@seller_required
def sales_report(request):
    seller = SellerProfile.objects.get(user=request.user)
    orders = Order.objects.filter(seller=seller, status="delivered")
    total_revenue = sum(order.total_amount for order in orders)
    return render(request, "seller/sales_report.html", {"total_revenue": total_revenue, "orders": orders})


@login_required
@seller_required
def seller_foods(request):
    seller = SellerProfile.objects.get(user=request.user)
    foods = FoodItem.objects.filter(seller=seller)

    return render(request, "seller/seller_foods.html", {"foods": foods})


@login_required
@seller_required
def add_food(request):
    seller = SellerProfile.objects.get(user=request.user)
    categories = FoodCategory.objects.all()

    if request.method == "POST":
        category_id = request.POST.get("category")

        if not category_id:
            messages.error(request, "Please select a food category")
            return redirect("add_food")

        category = get_object_or_404(FoodCategory, id=category_id)
        discount_percent = int(request.POST.get('discount_percent', 0))

        # Safety guard (business rule)
        if discount_percent < 0:
            discount_percent = 0
        if discount_percent > 90:
            discount_percent = 90

        FoodItem.objects.create(
            seller=seller,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            price=request.POST.get("price"),
            discount_percent=discount_percent,
            category=category,
            image=request.FILES.get("image"),
            is_available=True
        )
        messages.success(request, "Food item added")
        return redirect("seller_foods")

    categories = FoodCategory.objects.all()
    return render(request, "seller/add_food.html", {"categories": categories})


@login_required
@seller_required
def edit_food(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id, seller__user=request.user)
    food.discount_percent = int(request.POST.get('discount_percent', 0))
    food.save()

    categories = FoodCategory.objects.all()

    if request.method == "POST":
        food.name = request.POST.get("name")
        food.description = request.POST.get("description")
        food.price = request.POST.get("price")
        food.is_available = request.POST.get("is_available") == "on"

        category_id = request.POST.get("category")
        food.category = get_object_or_404(FoodCategory, id=category_id)

        if request.FILES.get("image"):
            food.image = request.FILES.get("image")
        food.save()
        messages.success(request, "Food updated")
        return redirect("seller_foods")

    return render(request, "seller/edit_food.html", {"food": food, "categories": categories})


@login_required
@seller_required
def delete_food(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id, seller__user=request.user)
    food.delete()
    messages.success(request, "Food deleted")
    return redirect("seller_foods")


@login_required
@seller_required
def seller_orders(request):
    seller = SellerProfile.objects.get(user=request.user)
    orders = Order.objects.filter(seller=seller).order_by("-created_at")
    return render(request, "seller/seller_orders.html", {"orders": orders})


@login_required
@seller_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, seller__user=request.user)

    if request.method == "POST":
        status = request.POST.get("status")
        order.status = status
        order.save()

        messages.success(request, "Order status updated")

        Notification.objects.create(
            user=order.customer.user,
            message=f"Your order #{order.id} is now {order.get_status_display()}"
        )

    return redirect("seller_orders")


def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        "total_customers": CustomerProfile.objects.count(),
        "total_sellers": SellerProfile.objects.count(),
        "total_orders": Order.objects.count(),
        "pending_sellers": SellerProfile.objects.filter(is_approved=False).count(),
        "approved_sellers": SellerProfile.objects.filter(is_approved=True).count(),
    }
    return render(request, "adminpanel/admin_dashboard.html", context)


@admin_required
def admin_sellers(request):
    sellers = SellerProfile.objects.all()
    return render(request, "adminpanel/admin_seller.html", {"sellers": sellers})


@admin_required
def approve_seller(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    seller.is_approved = True
    seller.save()
    Notification.objects.create(
        user=seller.user,
        message="Your seller account has been approved 🎉"
    )
    messages.success(request, "Seller approved successfully")
    return redirect("admin_sellers")


@admin_required
def reject_seller(request, seller_id):
    seller = get_object_or_404(SellerProfile, id=seller_id)
    seller.user.is_active = False
    seller.user.save()
    messages.success(request, "Seller rejected and account disabled")
    return redirect("adminpanel/admin_sellers")


@login_required
def notifications(request):
    notes = Notification.objects.filter(
        user=request.user).order_by("-created_at")
    return render(request, "customer/notifications.html", {"notifications": notes})


@login_required
def unread_notification_count(request):
    count = Notification.objects.filter(
        user=request.user, is_read=False).count()
    return JsonResponse({"count": count})


@login_required
def mark_notification_read(request, note_id):
    note = get_object_or_404(Notification, id=note_id, user=request.user)
    note.is_read = True
    note.save()
    return redirect("notifications")


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        customer__user=request.user
    )
    return render(request, "customer/order_tracking.html", {"order": order})


@login_required
def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty")
        return redirect("cart")

    customer = get_object_or_404(CustomerProfile, user=request.user)

    # Ensure single seller
    seller_ids = set()
    for item in cart.values():
        if "seller_id" not in item:
            messages.error(request, "Invalis cart data. Please re-add items.")
            request.session["cart"] = {}
            return redirect("cart")
        seller_ids.add(item["seller_id"])

    if len(seller_ids) != 1:
        messages.error(request, "You can order from only one seller at a time")
        return redirect("cart")

    seller = get_object_or_404(SellerProfile, id=list(seller_ids)[0])

    total = sum(item["price"] * item["quantity"] for item in cart.values())

    # Create Order
    order = Order.objects.create(
        customer=customer,
        seller=seller,
        total_amount=total,
        status="accepted"  # payment assumed successful
    )

    # Create Order Items
    for item in cart.values():
        OrderItem.objects.create(
            order=order,
            food_item_id=item["food_id"],
            quantity=item["quantity"],
            price=item["price"]
        )

    # Create MOCK Payment
    Payment.objects.create(
        order=order,
        amount=total,
        status="paid"
    )

    # Clear cart
    request.session["cart"] = {}

    messages.success(request, "Payment successful (Demo Mode)")
    return redirect("order_success")

# Complaint
@login_required
def add_complaint(request, seller_id):
    seller = User.objects.get(id=seller_id)

    if request.method == 'POST':
        Complaint.objects.create(
            customer=request.user,
            seller=seller,
            subject=request.POST['subject'],
            message=request.POST['message']
        )
        return redirect('customer_orders')

    return render(request, 'customer/add_complaint.html', {'seller': seller})


# admin complaint view

@login_required
def admin_complaints(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'admin/complaints.html', {'complaints': complaints})

# seller complaint view

@login_required
def seller_complaints(request):
    complaints = Complaint.objects.filter(seller=request.user)
    return render(request, 'seller/complaints.html', {'complaints': complaints})

# cusgtomer review
@login_required
def add_review(request, food_id):
    food = FoodItem.objects.get(id=food_id)

    if request.method == 'POST':
        Review.objects.create(
            customer=request.user,
            seller=food.seller,
            food_item=food,
            rating=request.POST['rating'],
            comment=request.POST.get('comment', '')
        )
        return redirect('order_history')

    return render(request, 'customer/add_review.html', {'food': food})

# seller Review

@login_required
def seller_reviews(request):
    reviews = Review.objects.filter(seller=request.user)
    return render(request, 'seller/reviews.html', {'reviews': reviews})

# admin review

def admin_reviews(request):
    reviews = Review.objects.all()
    return render(request, 'admin/reviews.html', {'reviews': reviews})
