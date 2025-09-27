from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth import get_user_model
from main.models import Customer,Notification
from ..models import Route

User = get_user_model()  # SuperUser

def home(request):
    return render(request, "home.html")

def login_view(request):
    if request.method == "POST":
        gst_number = request.POST.get("gst_number")
        password = request.POST.get("password")

        # First try SuperUser login
        user = authenticate(request, gst_number=gst_number, password=password)
        if user is not None:
            auth_login(request, user)
            if user.is_superuser:
                return redirect("admin_dashboard")
            else:
                return redirect("user_dashboard")

        # Else try Customer login
        try:
            customer = Customer.objects.get(gst_number=gst_number)
            if customer.check_password(password):
                # Store customer ID in session (since not Django auth user)
                request.session["customer_id"] = customer.id
                return redirect("user_dashboard")
            else:
                messages.error(request, "Invalid password for customer account")
        except Customer.DoesNotExist:
            messages.error(request, "Invalid GST number")

    return render(request, "auth/login.html")


def register(request):
    routes = Route.objects.all() 
    if request.method == "POST":
        name = request.POST.get("name")
        username = request.POST.get("username")
        gst_number = request.POST.get("gst_number")
        pincode = request.POST.get("pincode")
        address = request.POST.get("address")
        location = request.POST.get("location")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        try:
            customer = Customer(
                name=name,
                username=username,
                gst_number=gst_number,
                pincode=pincode,
                address=address,
                location=location

            )
            customer.set_password(password1)  # ✅ hash password
            customer.save()
            Notification.objects.create(
             message=f"New store registered: {customer.name}",
             type="customer"
            )

            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("register")

    return render(request, "auth/reg.html",{"routes": routes})


def logout_view(request):
    logout(request)  # clears Django session
    request.session.flush()  # clears customer session too
    return redirect("login")
