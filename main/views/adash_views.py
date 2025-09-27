from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.db.models import Q
from ..models import Product,Route,Order, Customer,Notification
from ..forms import ProductForm
from django.db.models import F, ExpressionWrapper, DecimalField,Sum
from collections import defaultdict
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, DecimalField, Sum, FloatField


# ✅ Restrict to superuser only
@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    # Notifications
    notifications = Notification.objects.order_by('-created_at')[:3]  # only latest 3
    unread_count = Notification.objects.filter(is_read=False).count()

    # Dashboard metrics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.annotate(
        revenue=F('quantity') * F('product__price')
    ).aggregate(total=Sum('revenue', output_field=FloatField()))['total'] or 0

    active_stores = Customer.objects.filter(order__isnull=False).distinct().count()
    inactive_stores = Customer.objects.count() - active_stores

    # Orders trend last 7 days
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    orders_per_day = [Order.objects.filter(created_at__date=d).count() for d in dates]
    orders_trend = list(zip(dates, orders_per_day))

    # Top 5 products
    top_products = Order.objects.values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "active_stores": active_stores,
        "inactive_stores": inactive_stores,
        "orders_trend": orders_trend,
        "top_products": top_products,
    }
    return render(request, "admin/home.html", context)




# -------------------- Pages --------------------
def orders(request):
    return render(request, "admin/orders.html")

def stores(request):
    return render(request, "admin/stores.html")

def payments(request):
    return render(request, "admin/payments.html")

def reports(request):
    return render(request, "admin/reports.html")

def settings(request):
    return render(request, "admin/settings.html")


# -------------------- Products --------------------
@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def product_list(request):
    query = request.GET.get("q")
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    else:
        products = Product.objects.all()
    return render(request, "admin/products.html", {"products": products})


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("products")
    else:
        form = ProductForm()
    return render(request, "admin/add_product.html", {"form": form})


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("products")
    else:
        form = ProductForm(instance=product)
    return render(request, "admin/edit_product.html", {"form": form})


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect("products")


# -------------------- Logout --------------------
def admin_logout(request):
    logout(request)
    return redirect("login")
#-----------routes-----------------
def routes_view(request):
    if request.method == "POST":
        day = request.POST.get("day")
        location = request.POST.get("location")
        if day and location:
            Route.objects.create(day=day, location=location)
        return redirect("routes")  # reload page after adding

    routes = Route.objects.all().order_by("day")
    return render(request, "admin/routes.html", {"routes": routes})

def delete_route(request, route_id):
    route = get_object_or_404(Route, id=route_id)
    route.delete()
    return redirect("routes")
#-----------order----------
@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)


def admin_orders(request):
    orders = Order.objects.select_related("customer", "product").all().order_by("-created_at")

    stores = defaultdict(list)
    for order in orders:
        stores[order.customer.name].append(order)

   
    grand_total = orders.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("product__price"),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    )["total"] or 0  

    return render(request, "admin/order.html", {
        "stores": dict(stores),
        "grand_total": grand_total,   
    })

def admin_stores(request):
    customers = Customer.objects.all()  # fetch all customers
    stores = []

    for customer in customers:
        stores.append({
            "id": customer.id,
            "store_name": customer.name,
            "owner_name": customer.username,
            "gst_number": customer.gst_number,
            "pincode": customer.pincode,
            "address": customer.address,
            "location": customer.location if customer.location else "Not assigned",
        })

    return render(request, "admin/stores.html", {"stores": stores})
def store_detail(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    return render(request, 'admin/store_detail.html', {'store': customer})


def delete_store(request, pk):
    customer = get_object_or_404(Customer, id=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('admin_stores')
    

#--------NOTIFICTAION---------
def notifications(request):
    notifications = Notification.objects.order_by('-created_at')[:10]
    return render(request, "admin/notifications.html", {
        "notifications": notifications
    })

def notifications_api(request):
    notifications = Notification.objects.order_by('-created_at')[:10]
    data = [
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_read": n.is_read,
        }
        for n in notifications
    ]
    return JsonResponse({"notifications": data})
def notification_redirect(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    notif.is_read = True   # mark as read
    notif.save()

    if notif.type == "customer":
        print("Redirecting to stores") 
        return redirect("admin_stores")
    elif notif.type == "order":
        return redirect("admin_orders")
    else:
        return redirect("admin_dashboard")

@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def admin_reports(request):
    # Top metrics
    total_orders = Order.objects.count()

    # Calculate total revenue dynamically using quantity * product price
    from django.db.models import F, Sum, FloatField
    total_revenue = Order.objects.annotate(
        revenue=F('quantity') * F('product__price')
    ).aggregate(total=Sum('revenue', output_field=FloatField()))['total'] or 0

    # New stores in last 30 days
    new_stores = Customer.objects.filter(
        id__in=Order.objects.filter(created_at__gte=timezone.now()-timedelta(days=30))
                  .values_list('customer_id', flat=True)
    ).count()

    # Active stores (placed orders)
    active_stores = Customer.objects.filter(order__isnull=False).distinct().count()

    # Inactive stores
    inactive_stores = Customer.objects.count() - active_stores

    # Orders trend (last 7 days)
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    orders_per_day = [Order.objects.filter(created_at__date=d).count() for d in dates]

    # Zip dates and orders for template
    orders_trend = list(zip(dates, orders_per_day))

    # Top 5 products
    top_products = Order.objects.values('product__name')\
        .annotate(total_qty=Sum('quantity'))\
        .order_by('-total_qty')[:5]

    context = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "new_stores": new_stores,
        "active_stores": active_stores,
        "inactive_stores": inactive_stores,
        "orders_trend": orders_trend,  # use this in template
        "top_products": top_products,
    }

    return render(request, "admin/reports.html", context)


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_superuser)
def notification_redirect(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    
    # Mark as read
    notif.is_read = True
    notif.save()

    # Redirect based on type
    if notif.type == "order":
        return redirect("admin_orders")   # your orders page url name
    elif notif.type == "customer":
        return redirect("admin_stores")   # your customers/stores page url name
    else:
        return redirect("admin_dashboard")