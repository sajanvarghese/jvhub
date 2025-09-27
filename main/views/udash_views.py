from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Product,Customer,Route,Order,Notification, CustomerNotification
from django.db.models import Q
from django.contrib import messages

def user_dashboard(request):
    query = request.GET.get("q")
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    else:
        products = Product.objects.all()
    return render(request, "users/user.html", {"products": products})
#----profile
def customer_profile(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")

    customer = get_object_or_404(Customer, id=customer_id)
    return render(request, "users/profile.html", {"customer": customer})
#--Edits

def edit_customer_profile(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")

    customer = get_object_or_404(Customer, id=customer_id)
    routes = Route.objects.all() 

    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.username = request.POST.get("username")
        customer.gst_number = request.POST.get("gst_number")
        customer.pincode = request.POST.get("pincode")
        customer.address = request.POST.get("address")
        customer.location = request.POST.get("location") 
        customer.save()
        return redirect("customer_profile")   # ✅ back to profile after save

    return render(request, "users/edit_profile.html", {"customer": customer,"routes": routes})

#----------orders
def order_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")  

    customer = get_object_or_404(Customer, id=customer_id)

    # Get delivery date based on customer's route
    route = Route.objects.filter(location=customer.location).first()
    delivery_date = next_delivery_date(route.day) if route else None

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))

        # Check minimum quantity
        if quantity < product.min_amount:
            messages.error(request, f"Minimum order is {product.min_amount} {product.Quantity}")
            return redirect("order_product", product_id=product.id)

        # Check stock availability
        if product.stock is not None and quantity > product.stock:
            messages.error(request, f"Only {product.stock} units available in stock")
            return redirect("order_product", product_id=product.id)

        # Create the order
        order = Order.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            delivery_date=delivery_date
        )

        # Subtract the ordered quantity from stock
        if product.stock is not None:
            product.stock -= quantity
            product.save(update_fields=["stock"])

        # Notification for admin
        Notification.objects.create(
            message=f"New order placed for {product.name} by {customer.name}",
            type="order"
        )

        # Notification for customer
        CustomerNotification.objects.create(
            customer=customer,
            order=order,
            message=f"Your order {product.name} has been placed successfully and will be delivered on {delivery_date}."
        )

        messages.success(request, "Order placed successfully!")
        return redirect("order_detail", order_id=order.id)

    return render(request, "users/order_product.html", {"product": product})


from main.utils import next_delivery_date
def order_detail(request, order_id):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login") 
    order = get_object_or_404(Order, id=order_id, customer__id=request.session.get("customer_id"))
    route = Route.objects.filter(location=order.customer.location).first()

    delivery_date = order.delivery_date  # reuse if already stored
    if route and not delivery_date:
        delivery_date = next_delivery_date(route.day)
        order.delivery_date = delivery_date
        order.save(update_fields=["delivery_date"])  # persist in DB

    return render(request, "users/order_detail.html", {
        "order": order,
        "route": route,
        "delivery_date": delivery_date,
    })
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from collections import defaultdict
from django.utils.timezone import localdate


def my_orders(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")
    today = localdate() 

    orders = Order.objects.filter(
        customer_id=customer_id,
        delivery_date__gte=today
    ).order_by("-created_at")

    # attach delivery_date for each order dynamically
    for order in orders:
        if not order.delivery_date:
            route = Route.objects.filter(location=order.customer.location).first()
            if route:
                order.delivery_date = next_delivery_date(route.day)
                order.save(update_fields=["delivery_date"])

    # grand total of all orders
    grand_total = orders.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("product__price"),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    )["total"] or 0
    grouped_orders = defaultdict(list)
    for order in orders:
        order_date = localdate(order.created_at)  
        grouped_orders[order_date].append(order)

    return render(request, "users/my_orders.html", {
        "orders": orders,
        "grouped_orders": grouped_orders,
        "grand_total": grand_total,
    })
def cancel_order(request, order_id):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")

    order = get_object_or_404(Order, id=order_id, customer_id=customer_id)

    # Optional: Prevent cancelling orders that have already been delivered
    today = localdate()
    if order.delivery_date and order.delivery_date < today:
        messages.error(request, "You cannot cancel an order that has already been delivered.")
        return redirect("my_orders")

    if request.method == "POST":
        order.delete()  # or set a 'cancelled' flag if you prefer
        messages.success(request, "Order cancelled successfully!")
        Notification.objects.create(
            message=f"Order for {order.product.name} by {order.customer.name} has been cancelled by the customer.",
            type="order"
        )
        return redirect("my_orders")

    # fallback redirect if someone accesses via GET
    return redirect("my_orders")

def customer_notifications(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")

    customer = get_object_or_404(Customer, id=customer_id)

    notifications = CustomerNotification.objects.filter(customer=customer).order_by("-created_at")

    # mark unread notifications as read
    CustomerNotification.objects.filter(customer=customer, is_read=False).update(is_read=True)

    return render(request, "users/customer_notifications.html", {
        "notifications": notifications
    })


# Mark single notification as read
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(CustomerNotification, id=notif_id)
    notif.is_read = True
    notif.save(update_fields=["is_read"])
    return redirect("customer_notifications")


# Mark all notifications as read
def mark_all_notifications_read(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("login")

    customer = get_object_or_404(Customer, id=customer_id)
    CustomerNotification.objects.filter(customer=customer, is_read=False).update(is_read=True)

    return redirect("customer_notifications")