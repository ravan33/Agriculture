"""
Views for the core application.
"""
import os
import csv
import json
import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.views.generic import (
    TemplateView, CreateView, DetailView, ListView, 
    UpdateView, FormView, DeleteView, View
)
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.db.models import Q, Count, Avg
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone

from .models import User, Query, Advice, AIDisease, Notification, InventoryItem, Rating
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, QueryForm, 
    AdviceForm, ProfileUpdateForm, AIDiagnosisForm, InventoryItemForm, RatingForm
)
from .session_utils import (
    session_management, terminate_session, terminate_all_sessions, session_info_ajax
)
from .utils import (
    predict_disease, create_notification, send_notification_email,
    get_crop_planning_content, get_available_crops, clean_disease_name
)
from .email_utils import (
    send_welcome_email, send_activation_email, send_new_advice_notification,
    send_query_received_notification, send_expert_new_query_notification,
    send_admin_user_registration_notification, send_password_reset_email
)
from .weather_service import get_weather_data, generate_weather_advice, get_weather_icon, get_weather_data_by_coordinates
from .market_service import (
    get_market_prices,
    get_market_summary,
    get_trending_crops,
    normalize_market_region,
)
from .signals import get_badge_info
from .chatbot_service import AgricultureChatbot

logger = logging.getLogger(__name__)
chatbot_service = AgricultureChatbot()


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Log out current user and redirect to landing page."""
    logout(request)
    return redirect('core:landing')


class LandingPageView(TemplateView):
    """
    Landing page for unauthenticated users.
    """
    template_name = 'landing.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'AgriVision AI - कृषि मित्र'
        return context


class CustomLoginView(LoginView):
    """
    Custom login view with enhanced styling and functionality.
    """
    form_class = CustomAuthenticationForm
    template_name = 'auth/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'प्रवेश - Login'
        return context
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')


class SignupView(CreateView):
    """
    User registration view.
    """
    form_class = CustomUserCreationForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('core:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'पंजीकरण - Signup'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Send welcome email to user
        send_welcome_email(self.object)
        
        # Send notification to admins
        send_admin_user_registration_notification(self.object)
        
        messages.success(
            self.request, 
            'खाता बनाया गया! Account created successfully! Admin approval pending.'
        )
        
        # Create notification for admin
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            create_notification(
                admin,
                'new_user_registration',
                'New User Registration',
                f'New {self.object.get_user_type_display()} account: {self.object.get_full_name()}'
            )
        return response


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view for authenticated users.
    """
    template_name = 'dashboard/base_dashboard.html'
    
    def get_template_names(self):
        # Check staff status first (admin dashboard)
        if self.request.user.is_staff:
            return ['dashboard/admin_dashboard.html']
        elif self.request.user.is_farmer:
            return ['dashboard/farmer_dashboard.html']
        elif self.request.user.is_expert:
            return ['dashboard/expert_dashboard.html']
        return [self.template_name]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_farmer:
            # Get weather data for farmer dashboard
            weather_data = None
            weather_advice = []
            if user.city:
                weather_data = get_weather_data(user.city)
                weather_advice = generate_weather_advice(weather_data)
            
            context.update({
                'page_title': 'Farmer Portal',
                'recent_queries': user.queries.all()[:5],
                'pending_queries_count': user.queries.filter(status='pending').count(),
                'answered_queries_count': user.queries.filter(status='answered').count(),
                'ai_diagnoses_count': user.ai_diagnoses.count(),
                'unread_notifications': user.notifications.filter(is_read=False)[:5],
                'weather_data': weather_data,
                'weather_advice': weather_advice,
                'weather_icon': get_weather_icon(weather_data.get('condition', '')) if weather_data else '🌤️',
                'badges': get_badge_info(),
                'user_badges': user.badges,
            })
        elif user.is_expert:
            context.update({
                'page_title': 'Salah Kendra - सलाह केंद्र',
                'pending_queries': Query.objects.filter(status='pending')[:5],
                'pending_count': Query.objects.filter(status='pending').count(),
                'my_advice_count': user.given_advice.count(),
                'recent_advice': user.given_advice.all()[:5],
                'unread_notifications': user.notifications.filter(is_read=False)[:5],
            })
        elif user.is_staff:
            # Get additional admin stats
            from datetime import timedelta
            recent_date = timezone.now() - timedelta(days=7)
            
            context.update({
                'page_title': 'Admin Dashboard',
                'total_users': User.objects.count(),
                'pending_users': User.objects.filter(is_active=False).count(),
                'total_queries': Query.objects.count(),
                'pending_queries': Query.objects.filter(status='pending').count(),
                'active_farmers': User.objects.filter(user_type='farmer', is_active=True).count(),
                'active_experts': User.objects.filter(user_type='expert', is_active=True).count(),
                'recent_registrations': User.objects.filter(date_joined__gte=recent_date).count(),
                'total_advice': Advice.objects.count(),
                'recent_advice': Advice.objects.filter(created_at__gte=recent_date).count(),
            })
        
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    User profile view.
    """
    template_name = 'dashboard/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Profile - मेरी प्रोफ़ाइल'
        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    """
    Update user profile view.
    """
    model = User
    form_class = ProfileUpdateForm
    template_name = 'dashboard/update_profile.html'
    success_url = reverse_lazy('core:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Update Profile - प्रोफ़ाइल अपडेट करें'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class CreateQueryView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create new query view (farmers only).
    """
    model = Query
    form_class = QueryForm
    template_name = 'query/create_query.html'
    success_url = reverse_lazy('core:query_history')
    
    def test_func(self):
        return self.request.user.is_farmer
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Agricultural Advisory'
        return context
    
    def form_valid(self, form):
        form.instance.farmer = self.request.user
        response = super().form_valid(form)
        
        # Send confirmation email to farmer
        send_query_received_notification(self.object)
        
        # Notify experts about new query
        experts = User.objects.filter(user_type='expert', is_active=True)
        for expert in experts:
            create_notification(
                expert,
                'new_query',
                'New Query Available',
                f'New query from {self.object.farmer.get_full_name()}: {self.object.title}'
            )
            # Send email notification to experts
            send_expert_new_query_notification(expert, self.object)
        
        messages.success(self.request, 'Your query has been submitted successfully!')
        return response


class QueryDetailView(LoginRequiredMixin, DetailView):
    """
    Query detail view with advice responses.
    """
    model = Query
    template_name = 'query/query_detail.html'
    context_object_name = 'query'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Query Details - {self.object.title[:30]}'
        context['advice_responses'] = self.object.advice_responses.all()
        return context


class QueryListView(LoginRequiredMixin, ListView):
    """
    List all queries (for experts and admin).
    """
    model = Query
    template_name = 'query/query_list.html'
    context_object_name = 'queries'
    paginate_by = 10
    
    def get_queryset(self):
        return Query.objects.select_related('farmer').prefetch_related('advice_responses')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'All Queries - सभी प्रश्न'
        return context


class QueryHistoryView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Query history for farmers.
    """
    model = Query
    template_name = 'query/query_history.html'
    context_object_name = 'queries'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_farmer
    
    def get_queryset(self):
        return self.request.user.queries.prefetch_related('advice_responses')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Queries'
        
        # Calculate query statistics
        user_queries = self.request.user.queries.all()
        context['total_queries'] = user_queries.count()
        context['pending_queries'] = user_queries.filter(status='pending').count()
        context['answered_queries'] = user_queries.filter(status='answered').count()
        context['closed_queries'] = user_queries.filter(status='closed').count()
        
        return context


class PendingQueriesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Pending queries view for experts.
    """
    model = Query
    template_name = 'expert/pending_queries.html'
    context_object_name = 'queries'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_expert
    
    def get_queryset(self):
        return Query.objects.filter(status='pending').select_related('farmer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Pending Queries - लंबित प्रश्न'
        return context


class ProvideAdviceView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Provide advice for a query (experts only).
    """
    model = Advice
    form_class = AdviceForm
    template_name = 'expert/provide_advice.html'
    
    def test_func(self):
        return self.request.user.is_expert
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = get_object_or_404(Query, id=self.kwargs['query_id'])
        context['query'] = query
        context['page_title'] = f'Provide Advice - सलाह दें'
        return context
    
    def form_valid(self, form):
        query = get_object_or_404(Query, id=self.kwargs['query_id'])
        form.instance.query = query
        form.instance.expert = self.request.user
        response = super().form_valid(form)
        
        # Notify farmer about new advice
        create_notification(
            query.farmer,
            'advice_received',
            'Advice Received',
            f'Expert {self.request.user.get_full_name()} has provided advice for your query: {query.title}'
        )
        
        # Send professional email notification to farmer
        send_new_advice_notification(query, self.object)
        
        messages.success(self.request, 'Your advice has been submitted successfully!')
        return redirect('core:pending_queries')


class MyAdviceView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List of advice given by expert.
    """
    model = Advice
    template_name = 'expert/my_advice.html'
    context_object_name = 'advice_list'
    paginate_by = 10
    
    def test_func(self):
        return self.request.user.is_expert
    
    def get_queryset(self):
        return self.request.user.given_advice.select_related('query', 'query__farmer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'My Advice - मेरी सलाह'
        return context


class AIDiagnosisView(LoginRequiredMixin, FormView):
    """
    AI disease diagnosis view with improved result display.
    """
    form_class = AIDiagnosisForm
    template_name = 'ai/diagnose.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Crop Guardian'
        
        # Check for recent diagnosis results to display
        if hasattr(self, 'diagnosis_result'):
            context['result'] = self.diagnosis_result
            context['clean_disease_name'] = self.clean_disease_name
            context['show_results'] = True
        
        return context
    
    def form_valid(self, form):
        # Create the diagnosis object but don't save yet
        ai_diagnosis = form.save(commit=False)
        ai_diagnosis.user = self.request.user
        
        # Save with default values first to get the image path
        ai_diagnosis.predicted_disease = "Processing..."
        ai_diagnosis.save()
        
        try:
            # Get image path
            image_path = ai_diagnosis.crop_image.path
            
            # Add logging for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Starting AI diagnosis for image: {image_path}")
            
            # Predict disease with improved error handling
            predicted_disease, confidence_score, remedies = predict_disease(image_path)
            
            logger.info(f"AI diagnosis completed: {predicted_disease}, confidence: {confidence_score}")
            
            # Update with actual results
            if predicted_disease and predicted_disease != "None":
                ai_diagnosis.predicted_disease = predicted_disease
                ai_diagnosis.confidence_score = confidence_score if confidence_score is not None else 0.0
                ai_diagnosis.remedies = remedies if remedies else "No specific remedies available."
            else:
                ai_diagnosis.predicted_disease = "Unknown Disease"
                ai_diagnosis.confidence_score = 0.0
                ai_diagnosis.remedies = "Unable to analyze the image. Please try with a clearer image or consult an expert."
            
            ai_diagnosis.save()
            
            # Store results for display without redirect
            self.diagnosis_result = ai_diagnosis
            self.clean_disease_name = clean_disease_name(ai_diagnosis.predicted_disease) if ai_diagnosis.predicted_disease else "Unknown"
            
            if predicted_disease and confidence_score and confidence_score > 0.1:
                messages.success(
                    self.request,
                    f'Disease detected: {self.clean_disease_name} (Confidence: {confidence_score:.1%})'
                )
            else:
                messages.warning(
                    self.request,
                    'Image analysis completed, but unable to determine disease with high confidence. Please consult an expert for accurate diagnosis.'
                )
                
        except Exception as e:
            # Handle any errors during prediction
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error during AI diagnosis: {e}")
            
            ai_diagnosis.predicted_disease = "Analysis Error"
            ai_diagnosis.confidence_score = 0.0
            ai_diagnosis.remedies = f"Error occurred during analysis: {str(e)}. Please try again or consult an expert."
            ai_diagnosis.save()
            
            messages.error(
                self.request,
                'An error occurred during image analysis. Please try again or consult an expert.'
            )
            
            # Store error results for display
            self.diagnosis_result = ai_diagnosis
            self.clean_disease_name = 'Analysis Error'
        
        # Return to the same page but with results displayed (no redirect)
        return self.render_to_response(self.get_context_data(form=form))


class AIDiagnosisHistoryView(LoginRequiredMixin, ListView):
    """
    AI diagnosis history for users.
    """
    model = AIDisease
    template_name = 'ai/history.html'
    context_object_name = 'diagnoses'
    paginate_by = 10
    
    def get_queryset(self):
        return self.request.user.ai_diagnoses.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'AI Diagnosis History - इतिहास'
        return context


class CropLibraryView(TemplateView):
    """
    Crop library main page.
    """
    template_name = 'library/crop_library.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Fasal Gyan - फसल ज्ञान'
        context['available_crops'] = get_available_crops()
        return context


class CropDetailView(TemplateView):
    """
    Individual crop detail page.
    """
    template_name = 'library/crop_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        crop_name = kwargs.get('crop_name')
        context['crop_name'] = crop_name
        context['page_title'] = f'{crop_name} - Crop Information'
        context['crop_content'] = get_crop_planning_content(crop_name)
        return context


class NotificationListView(LoginRequiredMixin, ListView):
    """
    User notifications list.
    """
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return self.request.user.notifications.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Notifications - सूचनाएं'
        return context


class MarkNotificationReadView(LoginRequiredMixin, DetailView):
    """
    Mark notification as read.
    """
    model = Notification
    
    def get_queryset(self):
        return self.request.user.notifications.all()
    
    def get(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """
    Mark all notifications as read for the current user.
    """
    
    def post(self, request, *args, **kwargs):
        # Update all unread notifications for the current user
        updated_count = request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({
            'success': True,
            'updated_count': updated_count
        })


class CustomPasswordResetView(PasswordResetView):
    """
    Custom password reset view that uses our HTML email template.
    """
    template_name = 'auth/password_reset.html'
    success_url = reverse_lazy('core:password_reset_done')
    
    def form_valid(self, form):
        """
        Override to use our custom email sending function.
        """
        email = form.cleaned_data["email"]
        
        # Find active users with this email
        users = User.objects.filter(email__iexact=email, is_active=True)
        
        for user in users:
            # Generate password reset token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_link = self.request.build_absolute_uri(
                reverse('core:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send custom HTML email
            send_password_reset_email(user, reset_link)
        
        # Don't call super().form_valid() to avoid Django's default email
        return redirect(self.success_url)


# =============================================================================
# NEW FEATURES VIEWS
# =============================================================================

class MarketPricesView(LoginRequiredMixin, TemplateView):
    """
    Real-time market prices view showing current crop prices with AJAX functionality.
    """
    template_name = 'market/prices.html'
    
    def get_context_data(self, **kwargs):
        import datetime
        
        context = super().get_context_data(**kwargs)
        market_region = normalize_market_region(self.request.GET.get('region'))
        
        # Get real-time market data
        market_data = get_market_prices(region=market_region)
        
        # Calculate summary statistics
        total_crops = len(market_data)
        trending_up = sum(1 for p in market_data if p.get('trend') == 'up')
        trending_down = sum(1 for p in market_data if p.get('trend') == 'down')
        stable = total_crops - trending_up - trending_down
        
        context.update({
            'page_title': 'Real-time Market Prices',
            'market_prices': market_data,
            'market_region': market_region,
            'market_region_options': [
                {'value': 'india', 'label': 'India'},
                {'value': 'us', 'label': 'United States'},
                {'value': 'uk', 'label': 'United Kingdom'},
            ],
            'summary': {
                'total_crops': total_crops,
                'trending_up': trending_up,
                'trending_down': trending_down,
                'stable': stable,
            },
            'last_updated': datetime.datetime.now().strftime("%I:%M %p"),
        })
        return context


class ChatbotView(LoginRequiredMixin, TemplateView):
    """Multilingual farming assistant page."""
    template_name = 'chatbot/chatbot.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Smart Farming Chatbot',
            'chatbot_model': chatbot_service.model and 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' or 'keyword-fallback',
        })
        return context


class ExpertLeaderboardView(LoginRequiredMixin, TemplateView):
    """
    Expert leaderboard showing top-rated experts.
    """
    template_name = 'expert/leaderboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get experts with their average ratings and advice counts
        experts = User.objects.filter(
            user_type='expert',
            is_active=True
        ).annotate(
            avg_rating=Avg('given_advice__rating__score'),
            advice_count=Count('given_advice')
        ).filter(
            advice_count__gt=0
        ).order_by('-avg_rating', '-advice_count')
        
        context.update({
            'page_title': 'Expert Leaderboard - विशेषज्ञ लीडरबोर्ड',
            'experts': experts,
            'badges': get_badge_info(),
        })
        return context


class ExpertWeatherInsightsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Weather insights tool for experts to provide better farming advice.
    """
    template_name = 'expert/weather_insights.html'
    
    def test_func(self):
        return self.request.user.is_expert or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Weather Insights - मौसम अंतर्दृष्टि',
            'available_cities': [
                'Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore', 'Hyderabad',
                'Pune', 'Ahmedabad', 'Surat', 'Jaipur', 'Lucknow', 'Kanpur',
                'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Pimpri-Chinchwad',
                'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 'Nashik'
            ]
        })
        return context


class ExpertCropCalculatorView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Crop calculator tool for experts to calculate fertilizer doses, seed rates, and yields.
    """
    template_name = 'expert/crop_calculator.html'
    
    def test_func(self):
        return self.request.user.is_expert or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Crop Calculator',
            'crop_types': [
                {'name': 'Rice'},
                {'name': 'Wheat'},
                {'name': 'Cotton'},
                {'name': 'Sugarcane'},
                {'name': 'Maize'},
                {'name': 'Soybean'},
                {'name': 'Groundnut'},
                {'name': 'Turmeric'},
                {'name': 'Chilies'},
                {'name': 'Red Gram'}
            ]
        })
        return context


class ExpertDiseaseReferenceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Disease reference database for experts to identify crop diseases and pests.
    """
    template_name = 'expert/disease_reference.html'
    
    def test_func(self):
        return self.request.user.is_expert or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Common crop diseases database
        disease_categories = {
            'fungal': [
                {'name': 'Leaf Blight', 'hindi': 'पत्ती का झुलसा', 'crops': ['Rice', 'Wheat', 'Maize']},
                {'name': 'Rust', 'hindi': 'रस्ट रोग', 'crops': ['Wheat', 'Coffee', 'Sugarcane']},
                {'name': 'Powdery Mildew', 'hindi': 'चूर्णी फफूंदी', 'crops': ['Grape', 'Cucumber', 'Wheat']},
                {'name': 'Black Rot', 'hindi': 'काला सड़न', 'crops': ['Cabbage', 'Cauliflower', 'Grape']},
                {'name': 'Anthracnose', 'hindi': 'एन्थ्रेकनोस', 'crops': ['Mango', 'Papaya', 'Tomato']}
            ],
            'bacterial': [
                {'name': 'Bacterial Blight', 'hindi': 'जीवाणु झुलसा', 'crops': ['Rice', 'Cotton', 'Bean']},
                {'name': 'Bacterial Wilt', 'hindi': 'जीवाणु म्लानि', 'crops': ['Tomato', 'Potato', 'Banana']},
                {'name': 'Fire Blight', 'hindi': 'अग्नि झुलसा', 'crops': ['Apple', 'Pear', 'Rose']},
                {'name': 'Bacterial Canker', 'hindi': 'जीवाणु कैंकर', 'crops': ['Tomato', 'Citrus', 'Stone fruits']}
            ],
            'viral': [
                {'name': 'Mosaic Virus', 'hindi': 'मोज़ेक वायरस', 'crops': ['Tobacco', 'Tomato', 'Cucumber']},
                {'name': 'Yellow Leaf Curl', 'hindi': 'पीली पत्ती मोड़', 'crops': ['Tomato', 'Chili', 'Okra']},
                {'name': 'Leaf Roll', 'hindi': 'पत्ती मोड़ना', 'crops': ['Potato', 'Sweet Potato', 'Grape']},
                {'name': 'Bunchy Top', 'hindi': 'गुच्छेदार शीर्ष', 'crops': ['Banana', 'Papaya']}
            ]
        }
        
        context.update({
            'page_title': 'Disease Reference Database - रोग संदर्भ डेटाबेस',
            'disease_categories': disease_categories,
            'total_diseases': sum(len(diseases) for diseases in disease_categories.values())
        })
        return context


@login_required
@require_http_methods(["GET", "POST"])
def expert_generate_disease_report(request):
    """
    Generate a comprehensive disease report for experts.
    """
    if not (request.user.is_expert or request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized access'}, status=403)
    
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            report_type = data.get('report_type', 'comprehensive')
            selected_categories = data.get('categories', ['fungal', 'bacterial', 'viral'])
            selected_crops = data.get('crops', [])
            
            # Disease database (same as in the view)
            disease_categories = {
                'fungal': [
                    {'name': 'Leaf Blight', 'hindi': 'पत्ती का झुलसा', 'crops': ['Rice', 'Wheat', 'Maize'], 
                     'severity': 'High', 'prevalence': 'Common', 'season': 'Monsoon',
                     'symptoms': 'Brown spots on leaves, wilting', 'treatment': 'Fungicide spray, crop rotation'},
                    {'name': 'Rust', 'hindi': 'रस्ट रोग', 'crops': ['Wheat', 'Coffee', 'Sugarcane'],
                     'severity': 'Medium', 'prevalence': 'Seasonal', 'season': 'Winter',
                     'symptoms': 'Orange-red pustules on leaves', 'treatment': 'Resistant varieties, fungicide'},
                    {'name': 'Powdery Mildew', 'hindi': 'चूर्णी फफूंदी', 'crops': ['Grape', 'Cucumber', 'Wheat'],
                     'severity': 'Medium', 'prevalence': 'Common', 'season': 'Dry season',
                     'symptoms': 'White powdery coating on leaves', 'treatment': 'Sulfur spray, proper ventilation'},
                    {'name': 'Black Rot', 'hindi': 'काला सड़न', 'crops': ['Cabbage', 'Cauliflower', 'Grape'],
                     'severity': 'High', 'prevalence': 'Rare', 'season': 'Rainy season',
                     'symptoms': 'Black lesions on leaves and fruits', 'treatment': 'Remove infected parts, copper fungicide'},
                    {'name': 'Anthracnose', 'hindi': 'एन्थ्रेकनोस', 'crops': ['Mango', 'Papaya', 'Tomato'],
                     'severity': 'High', 'prevalence': 'Common', 'season': 'Monsoon',
                     'symptoms': 'Dark sunken spots on fruits', 'treatment': 'Preventive fungicide, field sanitation'}
                ],
                'bacterial': [
                    {'name': 'Bacterial Blight', 'hindi': 'जीवाणु झुलसा', 'crops': ['Rice', 'Cotton', 'Bean'],
                     'severity': 'High', 'prevalence': 'Common', 'season': 'Monsoon',
                     'symptoms': 'Water-soaked lesions, yellowing', 'treatment': 'Copper bactericide, resistant varieties'},
                    {'name': 'Bacterial Wilt', 'hindi': 'जीवाणु म्लानि', 'crops': ['Tomato', 'Potato', 'Banana'],
                     'severity': 'Very High', 'prevalence': 'Common', 'season': 'Hot season',
                     'symptoms': 'Sudden wilting, vascular browning', 'treatment': 'Crop rotation, soil solarization'},
                    {'name': 'Fire Blight', 'hindi': 'अग्नि झुलसा', 'crops': ['Apple', 'Pear', 'Rose'],
                     'severity': 'High', 'prevalence': 'Seasonal', 'season': 'Spring',
                     'symptoms': 'Blackened shoots, cankers', 'treatment': 'Prune infected parts, streptomycin'},
                    {'name': 'Bacterial Canker', 'hindi': 'जीवाणु कैंकर', 'crops': ['Tomato', 'Citrus', 'Stone fruits'],
                     'severity': 'Medium', 'prevalence': 'Seasonal', 'season': 'Cool season',
                     'symptoms': 'Cankers on stems, leaf spots', 'treatment': 'Copper spray, sanitation'}
                ],
                'viral': [
                    {'name': 'Mosaic Virus', 'hindi': 'मोज़ेक वायरस', 'crops': ['Tobacco', 'Tomato', 'Cucumber'],
                     'severity': 'Medium', 'prevalence': 'Common', 'season': 'Year-round',
                     'symptoms': 'Mottled leaves, stunted growth', 'treatment': 'Remove infected plants, control vectors'},
                    {'name': 'Yellow Leaf Curl', 'hindi': 'पीली पत्ती मोड़', 'crops': ['Tomato', 'Chili', 'Okra'],
                     'severity': 'High', 'prevalence': 'Very Common', 'season': 'Hot season',
                     'symptoms': 'Curled yellowing leaves, stunting', 'treatment': 'Whitefly control, resistant varieties'},
                    {'name': 'Leaf Roll', 'hindi': 'पत्ती मोड़ना', 'crops': ['Potato', 'Sweet Potato', 'Grape'],
                     'severity': 'Medium', 'prevalence': 'Common', 'season': 'Growing season',
                     'symptoms': 'Upward rolling of leaves', 'treatment': 'Certified seed, aphid control'},
                    {'name': 'Bunchy Top', 'hindi': 'गुच्छेदार शीर्ष', 'crops': ['Banana', 'Papaya'],
                     'severity': 'Very High', 'prevalence': 'Regional', 'season': 'Year-round',
                     'symptoms': 'Stunted growth, bunched leaves', 'treatment': 'Remove infected plants, vector control'}
                ]
            }
            
            # Filter diseases based on selected categories and crops
            filtered_diseases = {}
            total_diseases = 0
            
            for category in selected_categories:
                if category in disease_categories:
                    if selected_crops:
                        # Filter by crops
                        filtered_diseases[category] = [
                            disease for disease in disease_categories[category]
                            if any(crop in disease['crops'] for crop in selected_crops)
                        ]
                    else:
                        filtered_diseases[category] = disease_categories[category]
                    total_diseases += len(filtered_diseases[category])
            
            # Generate statistics
            severity_stats = {'High': 0, 'Very High': 0, 'Medium': 0, 'Low': 0}
            prevalence_stats = {'Very Common': 0, 'Common': 0, 'Seasonal': 0, 'Rare': 0}
            season_stats = {'Monsoon': 0, 'Winter': 0, 'Summer': 0, 'Year-round': 0}
            
            all_diseases = []
            for category_diseases in filtered_diseases.values():
                all_diseases.extend(category_diseases)
            
            for disease in all_diseases:
                severity_stats[disease.get('severity', 'Medium')] += 1
                prevalence_stats[disease.get('prevalence', 'Common')] += 1
                season = disease.get('season', 'Year-round')
                if 'Hot' in season or 'Dry' in season:
                    season = 'Summer'
                elif 'Cool' in season or 'Spring' in season:
                    season = 'Winter'
                elif 'Growing' in season:
                    season = 'Year-round'
                season_stats[season] += 1
            
            # Generate report data
            report_data = {
                'report_metadata': {
                    'generated_by': request.user.get_full_name() or request.user.username,
                    'generated_on': timezone.now().isoformat(),
                    'report_type': report_type,
                    'total_diseases': total_diseases,
                    'categories_included': selected_categories,
                    'crops_filter': selected_crops if selected_crops else 'All crops'
                },
                'executive_summary': {
                    'total_diseases_analyzed': total_diseases,
                    'categories_covered': len(filtered_diseases),
                    'high_risk_diseases': severity_stats.get('High', 0) + severity_stats.get('Very High', 0),
                    'most_common_season': max(season_stats, key=season_stats.get) if season_stats else 'N/A'
                },
                'disease_categories': filtered_diseases,
                'statistics': {
                    'by_severity': severity_stats,
                    'by_prevalence': prevalence_stats,
                    'by_season': season_stats
                },
                'recommendations': [
                    'Implement integrated disease management (IDM) practices',
                    'Regular field monitoring and early detection systems',
                    'Use resistant varieties where available',
                    'Maintain field sanitation and crop rotation',
                    'Follow proper pesticide application schedules',
                    'Educate farmers about disease identification',
                    'Establish disease surveillance networks',
                    'Promote biological control methods'
                ]
            }
            
            return JsonResponse({
                'success': True,
                'report_data': report_data,
                'download_ready': True
            })
        
        # Handle GET request - return form options
        return JsonResponse({
            'success': True,
            'available_crops': [
                'Rice', 'Wheat', 'Cotton', 'Maize', 'Tomato', 'Potato', 
                'Sugarcane', 'Soybean', 'Banana', 'Mango', 'Apple', 
                'Grape', 'Cucumber', 'Cabbage', 'Bean', 'Chili'
            ],
            'report_types': [
                {'value': 'comprehensive', 'label': 'Comprehensive Report'},
                {'value': 'summary', 'label': 'Executive Summary'},
                {'value': 'by_crop', 'label': 'Crop-Specific Report'},
                {'value': 'seasonal', 'label': 'Seasonal Disease Report'}
            ]
        })
        
    except Exception as e:
        logger.error(f"Error generating disease report: {e}")
        return JsonResponse({'error': 'Failed to generate report'}, status=500)


class InventoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Inventory management list view (farmers only).
    """
    model = InventoryItem
    template_name = 'inventory/inventory_list.html'
    context_object_name = 'inventory_items'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_farmer
    
    def get_queryset(self):
        return InventoryItem.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Mera Stock - मेरा स्टॉक'
        return context


class InventoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create new inventory item view (farmers only).
    """
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/inventory_form.html'
    success_url = reverse_lazy('core:inventory_list')
    
    def test_func(self):
        return self.request.user.is_farmer
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Inventory item added successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Add Inventory Item - नया आइटम जोड़ें',
            'form_title': 'Add New Item'
        })
        return context


class InventoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update inventory item view (farmers only).
    """
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'inventory/inventory_form.html'
    success_url = reverse_lazy('core:inventory_list')
    
    def test_func(self):
        return (self.request.user.is_farmer and 
                self.get_object().user == self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Inventory item updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Update Inventory Item - आइटम अपडेट करें',
            'form_title': 'Update Item'
        })
        return context


class InventoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete inventory item view (farmers only).
    """
    model = InventoryItem
    template_name = 'inventory/inventory_confirm_delete.html'
    success_url = reverse_lazy('core:inventory_list')
    
    def test_func(self):
        return (self.request.user.is_farmer and 
                self.get_object().user == self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Inventory item deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Delete Inventory Item - आइटम हटाएं'
        return context


class GeneratePDFView(LoginRequiredMixin, DetailView):
    """
    Generate PDF report for a query and its advice.
    """
    model = Query
    
    def get_queryset(self):
        if self.request.user.is_farmer:
            return Query.objects.filter(farmer=self.request.user)
        elif self.request.user.is_expert:
            return Query.objects.filter(
                advice_responses__expert=self.request.user
            ).distinct()
        else:
            return Query.objects.all()
    
    def get(self, request, *args, **kwargs):
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            messages.error(request, 'PDF generation is not available. Please contact support.')
            return redirect('core:query_detail', pk=kwargs['pk'])
        
        query = self.get_object()
        advice_responses = query.advice_responses.all()
        
        # Render HTML template
        html_string = render_to_string('reports/report_template.html', {
            'query': query,
            'advice_responses': advice_responses,
            'now': timezone.now(),
        })
        
        # Generate PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="query_{query.id}_report.pdf"'
        
        return response


@login_required
def rate_advice(request, advice_id):
    """
    AJAX view for rating expert advice.
    """
    if request.method == 'POST' and request.user.is_farmer:
        advice = get_object_or_404(Advice, id=advice_id)
        
        # Check if user can rate this advice (must be the farmer who asked the question)
        if advice.query.farmer != request.user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        # Check if already rated
        existing_rating = Rating.objects.filter(
            advice=advice, 
            farmer=request.user
        ).first()
        
        if existing_rating:
            return JsonResponse({
                'success': False, 
                'error': 'You have already rated this advice'
            })
        
        try:
            score = int(request.POST.get('score'))
            comment = request.POST.get('comment', '').strip()
            
            if score not in [1, 2, 3, 4, 5]:
                return JsonResponse({'success': False, 'error': 'Invalid rating score'})
            
            # Create rating
            rating = Rating.objects.create(
                advice=advice,
                farmer=request.user,
                score=score,
                comment=comment
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
            
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid data'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_weather_by_location(request):
    """
    AJAX endpoint to get weather data by coordinates.
    Supports both GET (query params) and POST (JSON) methods.
    """
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            lat = request.GET.get('lat')
            lon = request.GET.get('lon')
        else:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lon = data.get('longitude')
        
        if not lat or not lon:
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        # Convert to float
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid coordinate format'}, status=400)
        
        # Get weather data by coordinates
        weather_data = get_weather_data_by_coordinates(lat, lon)
        
        if weather_data:
            weather_advice = generate_weather_advice(weather_data)
            weather_icon = get_weather_icon(weather_data.get('condition', ''))
            
            # Update user's city if logged in
            if request.user.is_authenticated:
                request.user.city = weather_data.get('city', '')
                request.user.save()
            
            return JsonResponse({
                'success': True,
                'weather_data': weather_data,
                'weather_advice': weather_advice,
                'weather_icon': weather_icon
            })
        else:
            return JsonResponse({'error': 'Could not fetch weather data'}, status=500)
            
    except Exception as e:
        logger.error(f"Error in get_weather_by_location: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@require_http_methods(["GET"])
def get_real_time_market_prices_ajax(request):
    """
    AJAX endpoint to get real-time market prices.
    """
    try:
        logger.info("Fetching real-time market prices via AJAX")
        market_region = normalize_market_region(request.GET.get('region'))
        prices = get_market_prices(region=market_region)
        market_summary = get_market_summary(region=market_region)
        
        logger.info(f"Successfully fetched {len(prices)} market prices")
        
        return JsonResponse({
            'success': True,
            'prices': prices,
            'summary': market_summary,
            'region': market_region,
            'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Error fetching real-time market prices: {e}")
        return JsonResponse({'error': 'Could not fetch market data'}, status=500)


@login_required
@require_http_methods(["POST"])
def chatbot_message_ajax(request):
    """AJAX endpoint for multilingual chatbot answers."""
    try:
        payload = json.loads(request.body)
        user_message = (payload.get('message') or '').strip()
        market_region = (payload.get('market_region') or 'india').strip().lower()
        response_language = (payload.get('response_language') or 'en').strip().lower()

        if not user_message:
            return JsonResponse({'error': 'Message is required.'}, status=400)

        result = chatbot_service.get_response(
            message=user_message,
            user=request.user,
            market_region=market_region,
            response_language=response_language,
        )

        return JsonResponse({'success': True, 'response': result})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
    except Exception as exc:
        logger.error("Chatbot response error: %s", exc)
        return JsonResponse({'error': 'Failed to process chatbot message.'}, status=500)


@require_http_methods(["POST"])
def get_weather_by_gps(request):
    """AJAX endpoint to get weather data based on GPS coordinates."""
    try:
        payload = json.loads(request.body)
        latitude = float(payload.get('latitude'))
        longitude = float(payload.get('longitude'))

        if not latitude or not longitude:
            return JsonResponse({'error': 'Latitude and longitude required.'}, status=400)

        # Get weather data by coordinates
        weather_data = get_weather_data_by_coordinates(latitude, longitude)
        
        if not weather_data:
            return JsonResponse({'error': 'Could not fetch weather data.'}, status=400)

        # Generate farming advice
        weather_advice = generate_weather_advice(weather_data)
        
        # Get weather icon
        weather_icon = get_weather_icon(weather_data.get('condition', ''))

        return JsonResponse({
            'success': True,
            'weather': weather_data,
            'advice': weather_advice,
            'icon': weather_icon
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid latitude/longitude values.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
    except Exception as exc:
        logger.error("Weather API error: %s", exc)
        return JsonResponse({'error': 'Failed to fetch weather data.'}, status=500)


@login_required
@require_http_methods(["POST"])
def chatbot_speak_response(request):
    """AJAX endpoint to generate speech audio for multilingual chatbot responses using gTTS."""
    try:
        import tempfile
        import os
        from django.http import FileResponse
        
        payload = json.loads(request.body)
        text = (payload.get('text') or '').strip()
        language = (payload.get('language') or 'en').strip().lower()

        if not text:
            return JsonResponse({'error': 'Text is required.'}, status=400)

        # Language code mapping for gTTS
        language_map = {
            'en': 'en',
            'hi': 'hi',
            'ta': 'ta',
            'te': 'te',
            'mr': 'mr',
            'bn': 'bn',
            'gu': 'gu',
            'kn': 'kn',
            'pa': 'pa',
        }

        # Try to use gTTS for multilingual support
        try:
            from gtts import gTTS
            
            lang_code = language_map.get(language, 'en')
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                output_file = temp_file.name
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=lang_code, slow=False, lang_check=False)
            tts.save(output_file)
            
            # Read and return the audio file
            response = FileResponse(open(output_file, 'rb'), content_type='audio/mpeg')
            response['Content-Disposition'] = f'inline; filename="response_{language}.mp3"'
            
            # Delete temp file after response
            def cleanup():
                try:
                    os.unlink(output_file)
                except:
                    pass
            response.close = cleanup
            
            return response
            
        except ImportError:
            logger.warning("gTTS not available, returning text for browser TTS")
            
            # Fallback: Return text with language code for browser TTS
            return JsonResponse({
                'success': True,
                'text': text,
                'language': language,
                'method': 'browser_tts'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
    except Exception as exc:
        logger.error("TTS generation error: %s", exc)
        return JsonResponse({
            'success': True,
            'text': text,
            'language': language,
            'method': 'browser_tts',
            'error_note': str(exc)
        })


@login_required
@require_http_methods(["POST"])
def expert_calculate_crop_requirements(request):
    """
    AJAX endpoint for crop calculator - calculate fertilizer, seeds, and yield.
    """
    if not (request.user.is_expert or request.user.is_staff):
        return JsonResponse({'error': 'Unauthorized access'}, status=403)
    
    try:
        # Debug logging
        logger.info(f"Crop calculator request from user: {request.user.username}")
        
        data = json.loads(request.body)
        logger.info(f"Received data: {data}")
        
        crop_type = data.get('crop_type')
        area = float(data.get('area', 0))  # in acres
        soil_type = data.get('soil_type', 'loamy')
        season = data.get('season', 'kharif')
        
        if not crop_type or area <= 0:
            logger.error(f"Invalid input: crop_type={crop_type}, area={area}")
            return JsonResponse({'error': 'Invalid crop type or area'}, status=400)
        
        # Crop calculation database (simplified version)
        crop_data = {
            'Rice': {
                'seed_rate': 25,  # kg per acre
                'nitrogen': 120,  # kg per acre
                'phosphorus': 60,
                'potash': 40,
                'expected_yield': 2500,  # kg per acre
                'water_requirement': 1500,  # mm
                'growing_period': 120  # days
            },
            'Wheat': {
                'seed_rate': 40,
                'nitrogen': 150,
                'phosphorus': 75,
                'potash': 50,
                'expected_yield': 2000,
                'water_requirement': 450,
                'growing_period': 120
            },
            'Cotton': {
                'seed_rate': 1.5,  # kg per acre
                'nitrogen': 160,
                'phosphorus': 80,
                'potash': 80,
                'expected_yield': 400,  # kg cotton per acre
                'water_requirement': 700,
                'growing_period': 180
            },
            'Maize': {
                'seed_rate': 20,
                'nitrogen': 200,
                'phosphorus': 100,
                'potash': 60,
                'expected_yield': 3000,
                'water_requirement': 600,
                'growing_period': 100
            },
            'Sugarcane': {
                'seed_rate': 37500,  # pieces per acre (sets)
                'nitrogen': 300,
                'phosphorus': 150,
                'potash': 200,
                'expected_yield': 40000,  # kg per acre
                'water_requirement': 2000,
                'growing_period': 365
            },
            'Soybean': {
                'seed_rate': 30,
                'nitrogen': 40,  # Less nitrogen due to nitrogen fixation
                'phosphorus': 80,
                'potash': 60,
                'expected_yield': 1200,
                'water_requirement': 450,
                'growing_period': 100
            },
            'Groundnut': {
                'seed_rate': 35,
                'nitrogen': 25,  # Less nitrogen due to nitrogen fixation
                'phosphorus': 50,
                'potash': 75,
                'expected_yield': 1500,
                'water_requirement': 500,
                'growing_period': 100
            },
            'Turmeric': {
                'seed_rate': 2500,  # kg per acre (rhizomes)
                'nitrogen': 60,
                'phosphorus': 50,
                'potash': 120,
                'expected_yield': 8000,
                'water_requirement': 1000,
                'growing_period': 240
            },
            'Chilies': {
                'seed_rate': 0.3,  # kg per acre
                'nitrogen': 150,
                'phosphorus': 75,
                'potash': 75,
                'expected_yield': 6000,
                'water_requirement': 600,
                'growing_period': 150
            },
            'Red Gram': {
                'seed_rate': 10,
                'nitrogen': 25,  # Less nitrogen due to nitrogen fixation
                'phosphorus': 50,
                'potash': 25,
                'expected_yield': 800,
                'water_requirement': 650,
                'growing_period': 180
            }
        }
        
        if crop_type not in crop_data:
            return JsonResponse({'error': 'Crop data not available'}, status=400)
        
        crop_info = crop_data[crop_type]
        
        # Calculate requirements
        calculations = {
            'seed_requirement': crop_info['seed_rate'] * area,
            'fertilizer_requirements': {
                'nitrogen': crop_info['nitrogen'] * area,
                'phosphorus': crop_info['phosphorus'] * area,
                'potash': crop_info['potash'] * area,
                'urea': (crop_info['nitrogen'] * area) / 0.46,  # Urea contains 46% N
                'dap': (crop_info['phosphorus'] * area) / 0.46,  # DAP contains 46% P2O5
                'mop': (crop_info['potash'] * area) / 0.60   # MOP contains 60% K2O
            },
            'expected_yield': crop_info['expected_yield'] * area,
            'water_requirement': crop_info['water_requirement'] * area,
            'growing_period': crop_info['growing_period'],
            'estimated_cost': {
                'seeds': calculations['seed_requirement'] * 50,  # Approximate seed cost per kg
                'fertilizers': (calculations['fertilizer_requirements']['nitrogen'] * 20 + 
                              calculations['fertilizer_requirements']['phosphorus'] * 30 + 
                              calculations['fertilizer_requirements']['potash'] * 25),
                'total': 0
            }
        }
        
        calculations['estimated_cost']['total'] = (
            calculations['estimated_cost']['seeds'] + 
            calculations['estimated_cost']['fertilizers']
        )
        
        # Soil-specific adjustments
        soil_adjustments = {
            'sandy': {'nitrogen': 1.2, 'phosphorus': 0.8, 'potash': 1.1},
            'clay': {'nitrogen': 0.9, 'phosphorus': 1.2, 'potash': 0.9},
            'loamy': {'nitrogen': 1.0, 'phosphorus': 1.0, 'potash': 1.0},
            'black': {'nitrogen': 0.8, 'phosphorus': 1.1, 'potash': 1.0}
        }
        
        if soil_type in soil_adjustments:
            adj = soil_adjustments[soil_type]
            for nutrient in ['nitrogen', 'phosphorus', 'potash']:
                calculations['fertilizer_requirements'][nutrient] *= adj[nutrient]
        
        logger.info(f"Successfully calculated requirements for {crop_type}, area: {area} acres")
        
        return JsonResponse({
            'success': True,
            'crop_type': crop_type,
            'area': area,
            'soil_type': soil_type,
            'season': season,
            'calculations': calculations,
            'recommendations': [
                f"सीड रेट: {calculations['seed_requirement']:.1f} kg seeds needed",
                f"नाइट्रोजन: {calculations['fertilizer_requirements']['nitrogen']:.1f} kg",
                f"फॉस्फोरस: {calculations['fertilizer_requirements']['phosphorus']:.1f} kg", 
                f"पोटाश: {calculations['fertilizer_requirements']['potash']:.1f} kg",
                f"यूरिया: {calculations['fertilizer_requirements']['urea']:.1f} kg",
                f"DAP: {calculations['fertilizer_requirements']['dap']:.1f} kg",
                f"MOP: {calculations['fertilizer_requirements']['mop']:.1f} kg",
                f"अपेक्षित उत्पादन: {calculations['expected_yield']:.0f} kg",
                f"पानी की आवश्यकता: {calculations['water_requirement']:.0f} liters",
                f"बढ़ने की अवधि: {calculations['growing_period']} days"
            ]
        })
        
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error in crop calculation: {e}")
        return JsonResponse({'error': 'Invalid calculation parameters'}, status=400)
    except Exception as e:
        logger.error(f"Error in expert crop calculator: {e}")
        return JsonResponse({'error': 'Calculation failed'}, status=500)


# =============================================================================
# ADMIN MANAGEMENT VIEWS
# =============================================================================

@login_required
@require_http_methods(["GET"])
def get_admin_users_ajax(request):
    from django.http import JsonResponse
    from .models import User

    users = []
    for user in User.objects.all():
        users.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'phone_number': getattr(user, 'phone_number', ''),
            'user_type': user.user_type,
            'user_type_display': user.get_user_type_display(),
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'queries_count': getattr(user, 'queries_count', 0),
            'advice_given_count': getattr(user, 'advice_given_count', 0),
            'advice_received_count': getattr(user, 'advice_received_count', 0),
        })

    return JsonResponse({'success': True, 'users': users})

def admin_user_report(request):
    """
    Generate a CSV report of all users for admin dashboard.
    """
    if not request.user.is_staff:
        return HttpResponse('Unauthorized', status=403)
    
    import csv
    from django.http import HttpResponse
    from .models import User

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Full Name', 'Email', 'Phone', 'Type', 'Status', 'Joined', 'Last Login', 'City', 'Address'])

    for user in User.objects.all().order_by('-date_joined'):
        writer.writerow([
            user.id,
            user.username,
            user.get_full_name(),
            user.email,
            getattr(user, 'phone_number', ''),
            user.get_user_type_display(),
            'Active' if user.is_active else 'Inactive',
            user.date_joined.strftime('%Y-%m-%d'),
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '',
            getattr(user, 'city', ''),
            getattr(user, 'address', ''),
        ])

    return response


@login_required
@require_http_methods(["GET"])
def get_user_details_ajax(request, user_id):
    """
    AJAX endpoint to get detailed user information for admin dashboard.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'phone_number': getattr(user, 'phone_number', ''),
            'user_type': user.user_type,
            'user_type_display': user.get_user_type_display(),
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'address': getattr(user, 'address', ''),
            'city': getattr(user, 'city', ''),
            'queries_count': user.queries.count() if hasattr(user, 'queries') else 0,
            'advice_given_count': user.given_advice.count() if hasattr(user, 'given_advice') else 0,
            'advice_received_count': 0,  # We can implement this later if needed
        }
        
        return JsonResponse({
            'success': True,
            'user': user_data
        })
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching user details: {e}")
        return JsonResponse({'error': 'Could not fetch user details'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_recent_users_ajax(request):
    """
    AJAX endpoint to get recent user registrations for admin dashboard.
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        from datetime import timedelta
        
        # Get users from last 7 days
        recent_date = timezone.now() - timedelta(days=7)
        recent_users = User.objects.filter(
            date_joined__gte=recent_date
        ).order_by('-date_joined')[:10]
        
        users_data = []
        for user in recent_users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'user_type_display': user.get_user_type_display(),
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'users': users_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching recent users: {e}")
        return JsonResponse({'error': 'Could not fetch recent users'}, status=500)


@login_required
@require_http_methods(["POST"])
def admin_bulk_user_action(request):
    """
    AJAX endpoint for bulk user actions (approve, reject, activate, deactivate).
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        action = data.get('action')
        user_ids = data.get('user_ids', [])
        
        if not action or not user_ids:
            return JsonResponse({'error': 'Missing action or user_ids'}, status=400)
        
        users = User.objects.filter(id__in=user_ids)
        count = 0
        
        for user in users:
            if action == 'approve' or action == 'activate':
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    count += 1
                    
                    # Send activation email
                    try:
                        from .email_utils import send_activation_email
                        send_activation_email(user)
                    except Exception as e:
                        logger.warning(f"Failed to send activation email to {user.email}: {e}")
                        
            elif action == 'reject' or action == 'deactivate':
                if user.is_active:
                    user.is_active = False
                    user.save()
                    count += 1
        
        # Create admin notification for the action
        create_notification(
            request.user,
            'admin_action',
            f'Bulk User Action Completed',
            f'Successfully {action}d {count} user(s)'
        )
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'Successfully {action}d {count} user(s)'
        })
        
    except Exception as e:
        logger.error(f"Error performing bulk user action: {e}")
        return JsonResponse({'error': 'Could not perform bulk action'}, status=500)

# Duplicate function removed - using the first get_user_details_ajax function

@csrf_exempt
@require_http_methods(["GET", "POST"])
def test_view(request):
    """
    Simple test view to check if forms and AJAX work
    """
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': 'POST request received successfully',
            'user_authenticated': request.user.is_authenticated,
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous'
        })
    
    return JsonResponse({
        'success': True,
        'message': 'GET request received successfully',
        'user_authenticated': request.user.is_authenticated,
        'user': str(request.user) if request.user.is_authenticated else 'Anonymous'
    })
