from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import (
    RegistrationView, UserNameValidationView, EmailValidationView,
    LoginView, LogoutView,
    role_list, role_create, role_edit, role_delete, role_clone, permission_overview,
    user_list, user_create, user_detail, user_edit, user_delete,
    user_toggle_status, user_lock, user_reset_password,
    user_change_role, user_export, user_audit,
    select_hostel,
    system_settings_view,
    module_list,
    module_create,
    module_edit,
    module_delete,
    hostel_management_list,
    hostel_management_create,
    hostel_management_edit,
    hostel_management_delete,
    # Legacy
    user_update_role,
)

urlpatterns = [
    # Auth
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('validate-username/', csrf_exempt(UserNameValidationView.as_view()), name='validate-username'),
    path('validate-email/', csrf_exempt(EmailValidationView.as_view()), name='validate_email'),

    # Role Management
    path('roles/', role_list, name='role_list'),
    path('roles/create/', role_create, name='role_create'),
    path('roles/edit/<int:pk>/', role_edit, name='role_edit'),
    path('roles/delete/<int:pk>/', role_delete, name='role_delete'),
    path('roles/<int:pk>/clone/', role_clone, name='role_clone'),
    path('api/user-permissions/<int:pk>/', permission_overview, name='permission_overview'),

    # User Management
    path('users/', user_list, name='user_management'),
    path('users/create/', user_create, name='user_create'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', user_delete, name='user_delete'),
    path('users/<int:pk>/toggle-status/', user_toggle_status, name='user_toggle_status'),
    path('users/<int:pk>/lock/', user_lock, name='user_lock'),
    path('users/<int:pk>/reset-password/', user_reset_password, name='user_reset_password'),
    path('users/<int:pk>/change-role/', user_change_role, name='user_change_role'),
    path('users/export/', user_export, name='user_export'),
    path('users/<int:pk>/audit/', user_audit, name='user_audit'),

    # Legacy (for existing sidebar link)
    path('users/update-role/<int:user_id>/', user_update_role, name='user_update_role'),
    path('select-hostel/<int:pk>/', select_hostel, name='select_hostel'),
    path('settings/system/', system_settings_view, name='system_settings_view'),
    path('modules/', module_list, name='module_list'),
    path('modules/create/', module_create, name='module_create'),
    path('modules/<int:pk>/edit/', module_edit, name='module_edit'),
    path('modules/<int:pk>/delete/', module_delete, name='module_delete'),

    # Hostel Management
    path('hostels/', hostel_management_list, name='hostel_management_list'),
    path('hostels/create/', hostel_management_create, name='hostel_management_create'),
    path('hostels/<int:pk>/edit/', hostel_management_edit, name='hostel_management_edit'),
    path('hostels/<int:pk>/delete/', hostel_management_delete, name='hostel_management_delete'),
]
