from django.urls import path
from .views import firm_list, edit_firm_flow
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_root, name='dashboard_root'),
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='dashboard_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard_login'), name='dashboard_logout'),
    path('firms/', firm_list, name='dashboard_firm_list'),
    path('firms/<int:firm_id>/edit-flow/', edit_firm_flow, name='edit_firm_flow'),
] 