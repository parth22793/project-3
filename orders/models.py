from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# Passing in a class into a class constructor extends it!
class Regular_Pizza(models.Model):
    name = models.CharField(max_length=64)
    small = models.DecimalField(max_digits=4, decimal_places=2)
    large = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'{self.name} - {self.small} - {self.large}')


class Sicilian_Pizza(models.Model):
    name = models.CharField(max_length=64)
    small = models.DecimalField(max_digits=4, decimal_places=2)
    large = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'{self.name} - {self.small} - {self.large}')


class Topping(models.Model):
    name=models.CharField(max_length=64)

    def __str__(self):
        return (f'{self.name}')


class Sub(models.Model):
    name = models.CharField(max_length=64)
      # Necessary because the Sausage, Peppers & Onions sub doesn't have a small size option!
    small = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    large = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'{self.name} - {self.small} - {self.large}')


class Pasta(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=4, decimal_places=2)
    
    def __str__(self):
        return (f'{self.name} - {self.price}')


class Salad(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'{self.name} - {self.price}')


class Dinner_Platter(models.Model):
    name = models.CharField(max_length=64)
    small = models.DecimalField(max_digits=4, decimal_places=2)
    large = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'{self.name} - {self.small} - {self.large}')


class Category(models.Model):
    """Contains names of items, like 'Regular Pizza', which become menu links"""
    name = models.CharField(max_length=64)

    def __str__(self):
        return (f'{self.name}')


class Order(models.Model):
    """Contains the main high-level info about the order, like who ordered it, state, number, etc."""
    # User is a foreign key because there is a 1-to-many relationship with orders (User may have multiple orders)

    # These two keys are enough to identify a unique order
    order_user = models.ForeignKey(User, on_delete=models.CASCADE)  # Delete the order if the user is removed
    order_number = models.IntegerField()

    toppings_left = models.IntegerField()
    state = models.CharField(max_length=64)

    def __str__(self):
        return (f'Order #{self.order_number} placed by {self.order_user}: toppings_left={self.toppings_left} : state={self.state}')


class Order_Items(models.Model):
    """A table of items and what orders they went with"""

    # Key off of order_number since these should be unique, the order is a foreign key
    order = models.ForeignKey(Order, on_delete=models.CASCADE)   # Delete order details if Order is deleted
    category = models.CharField(max_length=64)      # The type of item, e.g. "Sub"
    name = models.CharField(max_length=64)          # Printable name for cart, e.g. "Greek Salad"
    price = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return (f'#{self.order_number}: {self.category} - {self.name} - ${self.price}')