from django.urls import path
from .views import user_views, adash_views, udash_views

urlpatterns = [
    # user
    # path("", user_views.home, name="home"),
    path('', user_views.login_view, name="login"),
    path("register/", user_views.register, name="register"),
    path("logout/", user_views.logout_view, name="user_logout"),  # ✅ user logout

    # user dashboard
    # path("user_dashboard/", udash_views.user_dashboard, name="user_dashboard"),

    # admin dashboard
    path("admin-dashboard/", adash_views.admin_dashboard, name="admin_dashboard"),
    path("admin_logout/", adash_views.admin_logout, name="admin_logout"),  # ✅ admin logout
    path("admin/orders/", adash_views.admin_orders, name="admin_orders"),
    path('stores/', adash_views.admin_stores, name='admin_stores'),

    # products (search + CRUD)
    path("products/", adash_views.product_list, name="products"),  # ✅ single handler for list+search
    path("products/add/", adash_views.add_product, name="add_product"),
    path("products/edit/<int:pk>/", adash_views.edit_product, name="edit_product"),
    path("products/delete/<int:pk>/", adash_views.delete_product, name="delete_product"),

    # customer 
    path("user_dashboard/", udash_views.user_dashboard, name="user_dashboard"),

    path("routes/", adash_views.routes_view, name="routes"),
    path("routes/delete/<int:route_id>/", adash_views.delete_route, name="delete_route"),

    #-------profile----------
    path("profile/", udash_views.customer_profile, name="customer_profile"),
    path("profile/edit/", udash_views.edit_customer_profile, name="edit_customer_profile"),

    #-----orders------------
    path("order/<int:product_id>/", udash_views.order_product, name="order_product"),
    path("order-detail/<int:order_id>/", udash_views.order_detail, name="order_detail"),
    path("my-orders/", udash_views.my_orders, name="my_orders"),
    path('orders/cancel/<int:order_id>/', udash_views.cancel_order, name='cancel_order'),

    #-------stores---
    # urls.py
    path('store/<int:pk>/', adash_views.store_detail, name='store_detail'),
    path('store/delete/<int:pk>/', adash_views.delete_store, name='delete_store'),
    # NOTIFICATION
    path("admin-dashboard/notifications/", adash_views.notifications, name="admin_notifications"),
    path("admin-dashboard/notifications/api/", adash_views.notifications_api, name="admin_notifications_api"),
    path("admin-dashboard/notifications/<int:pk>/", adash_views.notification_redirect, name="notification_redirect"),
    path("admin/reports/", adash_views.admin_reports, name="admin_reports"),
    path('notification/<int:pk>/', adash_views.notification_redirect, name='notification_redirect'),
    #--------notifiction for customers
    path("notifications/", udash_views.customer_notifications, name="customer_notifications"),
    path("notifications/read/<int:notif_id>/", udash_views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all/", udash_views.mark_all_notifications_read, name="mark_all_notifications_read"),





]
