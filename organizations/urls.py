from django.urls import path
from . import views

urlpatterns = [
    # ── Organizations ──────────────────────────────────────────────────────────
    path('', views.org_list, name='org_list'),
    path('create/', views.org_create, name='org_create'),
    path('<int:pk>/edit/', views.org_edit, name='org_edit'),
    path('<int:pk>/delete/', views.org_delete, name='org_delete'),
    path('<int:pk>/toggle/', views.org_toggle_status, name='org_toggle_status'),
    path('<int:pk>/detail/', views.org_detail, name='org_detail'),
    path('<int:org_pk>/users/create/', views.org_user_create, name='org_user_create'),

    # ── Subscription Plans ─────────────────────────────────────────────────────
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:pk>/delete/', views.plan_delete, name='plan_delete'),

    # ── Subscriptions ──────────────────────────────────────────────────────────
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/assign/', views.assign_subscription, name='assign_subscription'),
    path('subscriptions/<int:pk>/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/pay/', views.org_subscription_pay, name='org_subscription_pay'),

    # ── White Label ────────────────────────────────────────────────────────────
    path('<int:org_pk>/whitelabel/', views.whitelabel_config, name='whitelabel_config'),

    # ── Analytics & Revenue ────────────────────────────────────────────────────
    path('analytics/global/', views.global_analytics, name='global_analytics'),
    path('revenue/', views.revenue_dashboard, name='revenue_dashboard'),

    # ── Support Tickets ────────────────────────────────────────────────────────
    path('support/tickets/', views.support_ticket_list, name='support_ticket_list'),
    path('support/tickets/<int:pk>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support/tickets/create/', views.support_ticket_create, name='support_ticket_create'),
    path('support/tickets/<int:pk>/update/', views.support_ticket_update, name='support_ticket_update'),

    # ── Org Settings ───────────────────────────────────────────────────────────
    path('<int:org_pk>/settings/', views.org_settings, name='org_settings'),
]
