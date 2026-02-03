from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
import json
import random

# Models & Forms
from insurance.models import Policy, InsuranceProduct, FAQ,Article
from accounts.models import Profile , Agent
from insurance.forms import PolicyPurchaseForm
from accounts.forms import  ProfileForm 
from claims.models import Claim
# --- PROFILE & DASHBOARD ---

@login_required
def profile_view(request):
    """View and update user profile."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'home/profile.html', {'form': form})

@login_required
def dashboard_view(request):
    """User dashboard with policies and claims."""
    user = request.user
    user_policies = Policy.objects.filter(user=user).order_by('expiry_date')
    user_claims = Claim.objects.filter(policy__in=user_policies).order_by('-date_filed')
    
    context = {
        'policies': user_policies,
        'claims': user_claims,
    }
    return render(request, 'home/dashboard.html', context)

# --- PUBLIC PAGES ---

def home_view(request):
    """Homepage with latest article and products."""
    latest_article = Article.objects.filter(is_active=True).order_by('-publication_date').first()
    featured_products = InsuranceProduct.objects.filter(is_active=True).order_by('product_type')[:3]
    return render(request, 'home/homepage.html', {'article': latest_article, 'products': featured_products})

def products_view(request):
    """Product catalog."""
    products = InsuranceProduct.objects.filter(is_active=True).order_by('name')
    return render(request, 'insurance/product_list.html', {'products': products})

def agents_view(request):
    """Agent finder."""
    city_query = request.GET.get('city')
    agents = Agent.objects.filter(is_active=True).order_by('city', 'name')
    if city_query:
        agents = agents.filter(city__icontains=city_query)
    unique_cities = Agent.objects.filter(is_active=True).values_list('city', flat=True).distinct().order_by('city')
    
    context = {'agents': agents, 'city_query': city_query, 'unique_cities': unique_cities}
    return render(request, 'home/agents.html', context)

def knowledge_hub_view(request):
    """FAQs and Articles."""
    faqs = FAQ.objects.filter(is_active=True).order_by('id')
    articles = Article.objects.filter(is_active=True).order_by('-publication_date')
    return render(request, 'home/knowledge_hub.html', {'faqs': faqs, 'articles': articles})

# --- TRANSACTIONS ---

@login_required
def purchase_policy_view(request):
    """Policy purchase logic."""
    user = request.user
    if request.method == 'POST':
        form = PolicyPurchaseForm(request.POST) 
        if form.is_valid():
            product = form.cleaned_data['product']
            start_date = form.cleaned_data['start_date']
            
            # Create Policy
            policy = form.save(commit=False)
            policy.user = user
            policy.premium_amount = product.base_premium + 1000 
            policy.policy_number = f"GMS-{random.randint(100000, 999999)}"
            policy.expiry_date = start_date + timezone.timedelta(days=365)
            policy.status = 'ACTIVE'
            policy.save()
            
            return redirect('dashboard')
    else:
        initial_data = {}
        product_id = request.GET.get('product_id')
        if product_id:
            try:
                initial_data['product'] = InsuranceProduct.objects.get(id=product_id)
            except InsuranceProduct.DoesNotExist: pass
        form = PolicyPurchaseForm(initial=initial_data)

    return render(request, 'home/purchase_policy.html', {'form': form})

# --- ADMIN ---

@user_passes_test(lambda u: u.is_superuser)
def admin_analytics_view(request):
    """Admin dashboard logic."""
    total_users = User.objects.count()
    total_policies = Policy.objects.count()
    
    today = timezone.now().date()
    renewal_window = today + timezone.timedelta(days=30)
    policies_expiring_soon = Policy.objects.filter(status='ACTIVE', expiry_date__gte=today, expiry_date__lte=renewal_window).count()
    
    claim_counts = Claim.objects.values('status').annotate(count=Count('status')).order_by('-count')
    claim_labels = [item['status'] for item in claim_counts]
    claim_data = [item['count'] for item in claim_counts]

    policy_type_counts = Policy.objects.values('product__product_type').annotate(count=Count('product__product_type')).order_by('-count')
    policy_type_labels = [item['product__product_type'] for item in policy_type_counts]
    policy_type_data = [item['count'] for item in policy_type_counts]
    
    policy_percentages = []
    if total_policies > 0:
        for item in policy_type_counts:
            percentage = round((item['count'] / total_policies) * 100, 1)
            policy_percentages.append(f"{item['product__product_type']} ({percentage}%)")

    last_week = timezone.now() - timezone.timedelta(days=7)
    recent_users = User.objects.filter(date_joined__gte=last_week).count()

    context = {
        'total_users': total_users,
        'total_policies': total_policies,
        'policies_expiring_soon': policies_expiring_soon,
        'recent_users': recent_users,
        'policy_percentages': policy_percentages,
        'claim_chart_labels': json.dumps(claim_labels),
        'claim_chart_data': json.dumps(claim_data),
        'policy_chart_labels': json.dumps(policy_type_labels),
        'policy_chart_data': json.dumps(policy_type_data),
    }
    return render(request, 'home/admin_analytics.html', context)