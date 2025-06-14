from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.dashboard_root, name='dashboard_root'),
    path('login/', views.DashboardLoginView.as_view(), name='dashboard_login'),
    path('logout/', LogoutView.as_view(next_page='dashboard_login'), name='dashboard_logout'),
    path('firms/', views.firm_list, name='dashboard_firm_list'),
    path('firms/<int:firm_id>/flow/', views.edit_firm_flow, name='dashboard_edit_firm_flow'),
] 