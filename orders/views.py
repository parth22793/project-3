from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Sum, Max

from .models import Regular_Pizza, Sicilian_Pizza, Topping, Sub, Pasta, Salad, Dinner_Platter, Category, Order, Order_Items

# Personal Touch: Stripe API
import stripe
import os

# Admin created outside of the code with:
# python manage.py createsuperuser --username=admin --email=admin@example.com
# (password: xxx)
# This code would never get checked into production!

# Stripe API
# Your API keys are always available in the Dashboard. For your convenience, your test API keys for your account are:

# Check for Stripe secret API key.
# These are Test values anyway.
if not os.getenv("STRIPE_API_KEY_SEC"):
    raise RuntimeError("STRIPE_API_KEY_SEC is not set")

# Don't get this over and over and over
stripe.api_key = os.getenv("STRIPE_API_KEY_SEC")


def index(request):
    if not request.user.is_authenticated:
        return render(request, "orders/login.html", {"message": None})

    # Build up the context of using the site
    order_number = Order.objects.get(order_user=request.user, state="initialized").order_number    # Get current cart that isn't pending or placed
    current_order = Order.objects.get(order_user=request.user, order_number=order_number)

    context = {
        "username": request.user,
        "order_number": order_number,
        "Categories": Category.objects.all(),   # For side Menu
        "Item_Categories": Order_Items.objects.filter(order=current_order).values_list('category').distinct(),    # Boiled down to list of unique categories e.g. Sub, Salad
        "Items": Order_Items.objects.filter(order=current_order),     # This is the entire DB row for any matching order number
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
        "Total": Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']
    }
    return render(request, "orders/index.html", context)


def menu(request, category):    # category is passed in the URL
    # Display the contents of each Category on the menu page
    
    # First need to map the link name to the Category object e.g. "Regular Pizza" --> "Regular_Pizza"
    # The "human names" like "Regular Pizza" come from whatever I typed into the database model as admin
    menu = getMenu(category)

    # Build up the context of using the site
    order_number = Order.objects.get(order_user=request.user, state="initialized").order_number    # Get current cart that isn't pending or placed
    current_order = Order.objects.get(order_user=request.user, order_number=order_number)

    context = {
        "Active_Category": category,            # The menu page they selected (e.g. Salad)
        "Menu": menu,                           # All DB entries for that category (e.g. [Greek Salad, Antipasto, etc.])
        "username": request.user,
        "order_number": order_number,
        "Categories": Category.objects.all(),   # For side Menu (e.g. [Regular Pizza, Sicilian Pizza, Toppings, etc.])
        "Item_Categories": Order_Items.objects.filter(order=current_order).values_list('category').distinct(),    # Boiled down to list of unique categories e.g. Sub, Salad
        "Items": Order_Items.objects.filter(order=current_order),     # This is the entire DB row for any matching order number
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
        "Total": Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']
    }
    # print("Context is:")
    # print(context)
    return render(request, "orders/menu.html", context)


def add(request, category, name, price):
    # When a user clicks on an item's (+) on the menu, add to cart

    # Again need to build common context for any page that renders base_layout.html
    menu = getMenu(category)
    order_number = Order.objects.get(order_user=request.user, state="initialized").order_number    # Get current cart that isn't pending or placed
    current_order = Order.objects.get(order_user=request.user, order_number=order_number)

    context = {
        "Active_Category": category,            # The menu page they selected (e.g. Salad)
        "Menu": menu,                           # All DB entries for that category (e.g. [Greek Salad, Antipasto, etc.])
        "username": request.user,
        "order_number": order_number,
        "Categories": Category.objects.all(),   # For side Menu (e.g. [Regular Pizza, Sicilian Pizza, Toppings, etc.])
        "Item_Categories": Order_Items.objects.filter(order=current_order).values_list('category').distinct(),    # Boiled down to list of unique categories e.g. Sub, Salad
        "Items": Order_Items.objects.filter(order=current_order),     # This is the entire DB row for any matching order number
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
        "Total": Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']
    }

    # Assign toppings budget (toppings_left) if they added a pizza
    if (category == "Regular Pizza" or category == "Sicilian Pizza"):
        if name == "1 Topping":
            current_order.toppings_left = 1
            current_order.save()
        elif name == "2 Toppings":
            current_order.toppings_left = 2
            current_order.save()
        elif name == "3 Toppings":
            current_order.toppings_left = 3
            current_order.save()
        # "Unlimited" toppings for Special (really 99,999 ;-)
        elif name == "Special":
            current_order.toppings_left = 99999
            current_order.save()
    # If they don't have any toppings_left (either didn't add a Pizza or added all toppings, return to main menu)
    if category == "Toppings" and current_order.toppings_left == 0:
        return render(request, "orders/menu.html", context)
    if category == "Toppings" and current_order.toppings_left > 0:
        current_order.toppings_left -= 1
        current_order.save()
    
    # Here is where we actually order the requested item (category, name, price) to the order items
    new_order_items = Order_Items(order=current_order, category=category, name=name, price=price)
    new_order_items.save()  # commit to DB

    # Update just anything in the context that changed (Order and Order_Items)
    # In Order_Items we added the item they clicked, so that context has changed
    # And in Order we potentially changed toppings_left, though that doesn't change the context of the page (no-op)
    context["Item_Categories"] = Order_Items.objects.filter(order=current_order).values_list('category').distinct()
    context["Items"] = Order_Items.objects.filter(order=current_order)
    context["Total"] = Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']

    return render(request, "orders/menu.html", context)


def place_order(request, order_number):
    current_order = Order.objects.get(order_user=request.user, order_number=order_number)

    context = {
        "place_order_view": "True",             # Suppress showing cart on the right when confirming orders
        "username": request.user,
        "order_number": order_number,
        "Categories": Category.objects.all(),   # For side Menu
        "Item_Categories": Order_Items.objects.filter(order=current_order).values_list('category').distinct(),    # Boiled down to list of unique categories e.g. Sub, Salad
        "Items": Order_Items.objects.filter(order=current_order),     # This is the entire DB row for any matching order number
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
        "Total": Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']
    }
    return render(request, "orders/place_order.html", context)


def confirm_order(request, order_number):
    # Get current order 
    current_order = Order.objects.get(order_user=request.user, order_number=order_number)

    # Get the total for the order, so we know what to charge
    total = Order_Items.objects.filter(order=current_order).aggregate(Sum('price'))['price__sum']

    # Grab the form info for Stripe charge
    # Creating Charges on Server side:  https://stripe.com/docs/charges
    token = request.POST.get('stripeToken')
    charge = stripe.Charge.create(
        amount=int(total * 100),   # this is in cents
        currency='usd',
        description='PiNOTchios Pizza',
        source=token,
    )

    # Don't change the cart status to placed until after the charge went through
    current_order.state = "placed"
    current_order.save()

    # Give them a new cart in case they want to buy again right away
    max_order_num = Order.objects.all().aggregate(Max('order_number'))['order_number__max']
    # print(f'max_order_num when order was placed: {max_order_num}')
        
    # Actually create the new shopping cart (order)
    new_order = Order(order_user=request.user, order_number=(max_order_num + 1), toppings_left=0, state="initialized")
    new_order.save()    # commit to table

    # Build up the context of using the site
    # and inform them the order was placed
    old_order_number = order_number
    order_number = max_order_num + 1
    
    context = {
        "message": (f'Order #{old_order_number} successfully placed.'),
        "username": request.user,
        "order_number": order_number,
        "Categories": Category.objects.all(),   # For side Menu
        "Item_Categories": Order_Items.objects.filter(order=new_order).values_list('category').distinct(),    # Boiled down to list of unique categories e.g. Sub, Salad
        "Items": Order_Items.objects.filter(order=new_order),     # This is the entire DB row for any matching order number
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
        "Total": Order_Items.objects.filter(order=new_order).aggregate(Sum('price'))['price__sum']
    }
    return render(request, "orders/index.html", context)


def register(request):
    # Registration should come through a submission form, POST request.
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_repeat = request.POST.get('password_repeat')
        # print(f'{username} {email} {password} {first_name} {last_name}')
        if not password == password_repeat:
            return render(request, "orders/register.html", {"message": "Passwords do not match."})
        user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
        user.save()     # Need to save the model, like a DB commit
        return render(request, "orders/login.html", {"message": "Successfully registered.  Please log in."})

    else:
        # A GET request means we got to the register page by clicking the link (from the Login page)
        return render(request, "orders/register.html")


# login and logout are Django.contrib libraries, so need to use different names for these views (urls.py)
def login_page(request):
    username=request.POST.get('username')
    password=request.POST.get('password')
    user=authenticate(request, username=username, password=password)

    # Valid user logged in
    if user is not None:
        login(request, user)

        # Everyone comes through the Login once, so create a blank cart for them then
        # Just set to an initialized state to indicate they haven't added anything (give an order number to their empty cart)

        # First, see if there is already a shopping cart for this user that hasn't been ordered yet
        user_cart_count = Order.objects.filter(order_user=user, state="initialized").count()
        # print(f'User has {user_cart_count} carts in initialized state')
        if user_cart_count == 0:
            # Only if they don't already have a cart they've started, assign a new one

            # Get current highest cart order number from database (no more global variable)
            max_order_num = Order.objects.all().aggregate(Max('order_number'))['order_number__max']
            # print(f'max_order_num before new order: {max_order_num}')
            # Create a new cart (order) for user, incrementing order_number by one
            new_order = Order(order_user=user, order_number=(max_order_num+1), toppings_left=0, state="initialized")
            new_order.save()    # commit to table
        if user_cart_count >= 2:
            print("Error!  User should not have gotten a new cart!")
        
        # Otherwise, user already has a cart
        
        # Reverse goes from the (potentially named, as in here) view to the URL (here "").
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "orders/login.html", {"message": "Invalid username or password."}) 


def logout_page(request):
    # Only way to log out is Logout link at top, GET request
    logout(request)
    return render(request, "orders/login.html", {"message": "Logged out."})


def getMenu(category):
    if category == "Regular Pizza":
        menu = Regular_Pizza.objects.all()
    elif category == "Sicilian Pizza":
        menu = Sicilian_Pizza.objects.all()
    elif category == "Toppings":
        menu = Topping.objects.all()
    elif category == "Subs":
        menu = Sub.objects.all()
    elif category == "Pasta":
        menu = Pasta.objects.all()
    elif category == "Salad":
        menu = Salad.objects.all()
    elif category == "Dinner Platters":
        menu = Dinner_Platter.objects.all()
    else:
        print(f"Error in getMenu(), undefined category item: {category}")
    return menu