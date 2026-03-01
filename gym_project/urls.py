"""
URL configuration for gym_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from administracion.views import (
    landing_page, admin_dashboard, admin_clientes, 
    admin_rutinas, admin_cliente_detail, admin_rutina_builder, 
    custom_login, register_user, logout_user
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing'),
    path('dashboard/', admin_dashboard, name='dashboard'),
    path('dashboard/clientes/', admin_clientes, name='admin_clientes'),
    path('dashboard/clientes/<int:pk>/', admin_cliente_detail, name='admin_cliente_detail'),
    path('dashboard/rutinas/', admin_rutinas, name='admin_rutinas'),
    path('dashboard/rutinas/crear/', admin_rutina_builder, name='admin_rutina_builder'),
    path('dashboard/rutinas/editar/<int:pk>/', admin_rutina_builder, name='admin_rutina_edit'),
    path('login/', custom_login, name='login'),
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
]
