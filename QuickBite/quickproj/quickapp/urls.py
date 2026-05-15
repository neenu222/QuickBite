from django.urls import path
from . import views

urlpatterns = [

    # Auth
    path('', views.login_view, name='login'),
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/seller/', views.register_seller, name='register_seller'),
    path('logout/', views.logout_view, name='logout'),

    # Customer
    path('customer', views.customer_home, name='customer_home'),
    path('food/<int:item_id>/', views.food_detail, name='food_detail'),
    path("orders/", views.customer_orders, name="customer_orders"),
    path("profile/", views.customer_profile, name="customer_profile"),
    path("profile/edit/", views.edit_customer_profile, name="edit_customer_profile"),
    # path('item/<int:item_id>/', views.item_details, name='item_details'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path("checkout/", views.checkout, name="checkout"),
    path("order-success/", views.order_success, name="order_success"),
    path('cart/increase/<int:item_id>/', views.increase_cart_quantity, name='increase_cart_quantity'),
    path('cart/decrease/<int:item_id>/', views.decrease_cart_item, name='cart_decrease'),
    path('complaint/add/<int:seller_id>/', views.add_complaint, name='add_complaint'),





    # SELLER PANEL
    path('seller/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/sales-report/', views.sales_report, name='sales_report'),
    path('seller/foods/', views.seller_foods, name='seller_foods'),
    path('seller/foods/add/', views.add_food, name='add_food'),
    path('seller/foods/edit/<int:food_id>/', views.edit_food, name='edit_food'),
    path('seller/foods/delete/<int:food_id>/', views.delete_food, name='delete_food'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),


    # Admin custom
    path('adminpanel/admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('adminpanel/sellers/', views.admin_sellers, name='admin_sellers'),
    path('adminpanel/customers/', views.admin_customers, name='admin_customer'),
    path('adminpanel/orders/', views.admin_orders, name='admin_orders'),
    path('adminpanel/complaints/', views.admin_complaints, name='admin_complaints'),
    path("adminpanel/sellers/pending", views.admin_seller_approval, name="admin_seller_approval"),
    path("adminpanel/seller/approve/<int:seller_id>/", views.approve_seller, name="approve_seller"),
    path("adminpanel/sellers/reject/<int:seller_id>/", views.reject_seller, name="reject_seller"),
    # Admin - Categories
    path("adminpanel/categories/", views.admin_categories, name="admin_categories"),
    path("adminpanel/categories/add/", views.add_category, name="add_category"),
    path("adminpanel/categories/edit/<int:category_id>/", views.edit_category, name="edit_category"),
    path("adminpanel/categories/delete/<int:category_id>/", views.delete_category, name="delete_category"),


    # notification
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/unread-count/", views.unread_notification_count, name="unread_notification_count"),
    path("notifications/read/<int:note_id>/", views.mark_notification_read, name="mark_notification_read"),
]
