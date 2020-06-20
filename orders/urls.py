from django.urls import path

from . import views

urlpatterns = [
    # URL pattern, Python function called, name used for reverse()
    path("", views.index, name="index"),
    path("login", views.login_page, name="login"),
    path("logout", views.logout_page, name="logout"),
    path("register", views.register, name="register"),
    path("menu/<str:category>", views.menu, name="menu"),
    path("add/<str:category>/<str:name>/<str:price>", views.add, name="add"),
    path("place_order/<str:order_number>", views.place_order, name="place_order"),
    path("confirm_order/<str:order_number>", views.confirm_order, name="confirm_order"),
]