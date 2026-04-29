"""
URL configuration for core app.
"""
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

# Authentication URLs
auth_urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'),
         name='password_reset_complete'),
]

# Dashboard URLs
dashboard_urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
]

# Query/Advice URLs
query_urlpatterns = [
    path('create/', views.CreateQueryView.as_view(), name='create_query'),
    path('<int:pk>/', views.QueryDetailView.as_view(), name='query_detail'),
    path('list/', views.QueryListView.as_view(), name='query_list'),
    path('history/', views.QueryHistoryView.as_view(), name='query_history'),
]

# Expert URLs
expert_urlpatterns = [
    path('pending/', views.PendingQueriesView.as_view(), name='pending_queries'),
    path('provide/<int:query_id>/', views.ProvideAdviceView.as_view(), name='provide_advice'),
    path('my-advice/', views.MyAdviceView.as_view(), name='my_advice'),
    path('leaderboard/', views.ExpertLeaderboardView.as_view(), name='expert_leaderboard'),
    path('weather-insights/', views.ExpertWeatherInsightsView.as_view(), name='expert_weather_insights'),
    path('crop-calculator/', views.ExpertCropCalculatorView.as_view(), name='expert_crop_calculator'),
    path('disease-reference/', views.ExpertDiseaseReferenceView.as_view(), name='expert_disease_reference'),
]

# Market URLs
market_urlpatterns = [
    path('prices/', views.MarketPricesView.as_view(), name='market_prices'),
]

# Inventory URLs
inventory_urlpatterns = [
    path('', views.InventoryListView.as_view(), name='inventory_list'),
    path('add/', views.InventoryCreateView.as_view(), name='inventory_create'),
    path('<int:pk>/edit/', views.InventoryUpdateView.as_view(), name='inventory_update'),
    path('<int:pk>/delete/', views.InventoryDeleteView.as_view(), name='inventory_delete'),
]

# Chatbot URLs
chatbot_urlpatterns = [
    path('', views.ChatbotView.as_view(), name='chatbot'),
]

# PDF and Rating URLs
misc_urlpatterns = [
    path('query/<int:pk>/pdf/', views.GeneratePDFView.as_view(), name='generate_pdf'),
    path('rate-advice/<int:advice_id>/', views.rate_advice, name='rate_advice'),
    path('ajax/weather-by-location/', views.get_weather_by_location, name='weather_by_location'),
    path('ajax/market-prices/', views.get_real_time_market_prices_ajax, name='market_prices_ajax'),
    path('ajax/expert/crop-calculator/', views.expert_calculate_crop_requirements, name='expert_crop_calculator_ajax'),
    path('ajax/expert/disease-report/', views.expert_generate_disease_report, name='expert_disease_report_ajax'),
    path('ajax/admin/users/', views.get_admin_users_ajax, name='admin_users_ajax'),
    path('ajax/admin/users/recent/', views.get_recent_users_ajax, name='admin_recent_users_ajax'),
    path('ajax/admin/users/bulk-action/', views.admin_bulk_user_action, name='admin_bulk_user_action'),
    path('ajax/admin/users/<int:user_id>/', views.get_user_details_ajax, name='admin_user_details_ajax'),
    path('ajax/admin/report/', views.admin_user_report, name='admin_user_report'),
    path('ajax/chatbot/message/', views.chatbot_message_ajax, name='chatbot_message_ajax'),
    path('ajax/chatbot/speak/', views.chatbot_speak_response, name='chatbot_speak_ajax'),
    path('ajax/weather/gps/', views.get_weather_by_gps, name='weather_gps_ajax'),
]

# Session Management URLs
session_urlpatterns = [
    path('sessions/', views.session_management, name='session_management'),
    path('ajax/session/terminate/', views.terminate_session, name='terminate_session'),
    path('ajax/session/terminate-all/', views.terminate_all_sessions, name='terminate_all_sessions'),
    path('ajax/session/info/', views.session_info_ajax, name='session_info_ajax'),
]

# AI Diagnosis URLs
ai_urlpatterns = [
    path('diagnose/', views.AIDiagnosisView.as_view(), name='ai_diagnose'),
    path('history/', views.AIDiagnosisHistoryView.as_view(), name='ai_history'),
]

# Crop Library URLs
library_urlpatterns = [
    path('', views.CropLibraryView.as_view(), name='crop_library'),
    path('<str:crop_name>/', views.CropDetailView.as_view(), name='crop_detail'),
]

# Notification URLs
notification_urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('mark-read/<int:pk>/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
]

# Main URL patterns
urlpatterns = [
    # Landing page
    path('', views.LandingPageView.as_view(), name='landing'),
    
    # Authentication
    path('auth/', include(auth_urlpatterns)),
    
    # Dashboard
    path('dashboard/', include(dashboard_urlpatterns)),
    
    # Queries and Advice
    path('query/', include(query_urlpatterns)),
    
    # Expert features
    path('expert/', include(expert_urlpatterns)),
    
    # AI Diagnosis
    path('ai/', include(ai_urlpatterns)),
    
    # Crop Library
    path('library/', include(library_urlpatterns)),
    
    # Notifications
    path('notifications/', include(notification_urlpatterns)),
    
    # Market features
    path('market/', include(market_urlpatterns)),
    
    # Inventory management
    path('inventory/', include(inventory_urlpatterns)),

    # Chatbot assistant
    path('chatbot/', include(chatbot_urlpatterns)),
    
    # Session Management
    path('account/', include(session_urlpatterns)),
    
    # Test endpoint
    path('test/', views.test_view, name='test'),
    
    # Miscellaneous features
    path('', include(misc_urlpatterns)),
]
