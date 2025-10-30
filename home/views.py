from django.shortcuts import render, redirect, get_object_or_404
from insurance.models import Policy, Claim, InsuranceProduct, Agent, FAQ
from insurance.forms import ClaimForm, PolicyPurchaseForm, ProfileForm
from django.http import Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone
import json
import random
from insurance.models import Policy, Claim, InsuranceProduct, Agent, FAQ, Profile, Article, ClaimStep # <-- FIX: Ensure Profile is here!
from insurance.forms import ClaimForm, PolicyPurchaseForm, ProfileForm 

@login_required
def profile_view(request):
    """
    Allows the logged-in user to view and update their personal profile information.
    """
    # Get the user's profile, creating it if it doesn't exist (though it should exist due to registration flow)
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Redirect back to dashboard (In a real app, use Django Messages for success alert)
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form
    }
    return render(request, 'home/profile.html', context)
def home_view(request):
    """
    Renders the main homepage.
    Fetches the latest article and 3 featured products for display.
    """
    # Fetch the single most recent, active article
    latest_article = Article.objects.filter(is_active=True).order_by('-publication_date').first()
    
    # Fetch a few key products to feature
    featured_products = InsuranceProduct.objects.filter(is_active=True).order_by('product_type')[:3]

    context = {
        'article': latest_article,
        'products': featured_products,
    }
    return render(request, 'home/homepage.html', context)
def products_view(request):
    """
    Fetches all active insurance products from the database to display in a catalog.
    """
    # We only want to show products that are currently being offered.
    products = InsuranceProduct.objects.filter(is_active=True).order_by('name')
    
    context = {
        'products': products
    }
    return render(request, 'home/products.html', context)

@login_required
def dashboard_view(request):
    """
    Fetches and displays all policies and claims for the currently logged-in user.
    """
    user = request.user
    
    # Fetch all policies owned by this user, ordering by expiry date
    user_policies = Policy.objects.filter(user=user).order_by('expiry_date')
    
    # Fetch all claims related to those policies
    user_claims = Claim.objects.filter(policy__in=user_policies).order_by('-date_filed')

    context = {
        'policies': user_policies,
        'claims': user_claims,
    }
    return render(request, 'home/dashboard.html', context)

def agents_view(request):
    """
    Fetches and displays active agents, optionally filtered by city.
    """
    city_query = request.GET.get('city') # Get the city name from the URL query parameters
    
    agents = Agent.objects.filter(is_active=True).order_by('city', 'name')
    
    if city_query:
        # Filter agents whose city name contains the query (case-insensitive)
        agents = agents.filter(city__icontains=city_query)
        
    # Get a list of unique cities to populate the dropdown filter on the page
    unique_cities = Agent.objects.filter(is_active=True).values_list('city', flat=True).distinct().order_by('city')

    context = {
        'agents': agents,
        'city_query': city_query,
        'unique_cities': unique_cities,
    }
    return render(request, 'home/agents.html', context)

@login_required
def file_claim_view(request):
    """
    Allows a logged-in user to file a claim against one of their active policies.
    """
    user = request.user
    
    if request.method == 'POST':
        # Pass the request.user to the form for validation/filtering
        form = ClaimForm(request.POST, user=user) 
        if form.is_valid():
            claim = form.save(commit=False)
            # The policy field is already set by the form data
            claim.status = 'FILED' # Automatically set status to 'Filed'
            claim.save()
            # Redirect to dashboard with a success message (Django messages framework needed for real message)
            return redirect('dashboard')
    else:
        # For GET request, initialize the form, passing the user object
        form = ClaimForm(user=user)

    context = {
        'form': form
    }
    return render(request, 'home/file_claim.html', context)

@login_required
def claim_detail_view(request, claim_id):
    """
    Shows detailed status and provides a step-by-step guide for the claim.
    """
    claim = get_object_or_404(Claim, id=claim_id)
    
    if claim.policy.user != request.user:
        raise Http404("You do not have permission to view this claim.")
    
    # --- NEW LOGIC: FETCH GUIDANCE STEPS ---
    product_type_of_claim = claim.policy.product.product_type
    guidance_steps = ClaimStep.objects.filter(product_type=product_type_of_claim)
        
    context = {
        'claim': claim,
        'policy': claim.policy,
        'guidance_steps': guidance_steps, # Pass the steps to the template
    }
    return render(request, 'home/claim_detail.html', context)
def knowledge_hub_view(request):
    """
    Fetches active FAQs and Articles for the knowledge hub page.
    """
    faqs = FAQ.objects.filter(is_active=True).order_by('id')
    articles = Article.objects.filter(is_active=True).order_by('-publication_date')
    
    context = {
        'faqs': faqs,
        'articles': articles,
    }
    return render(request, 'home/knowledge_hub.html', context)

@user_passes_test(lambda u: u.is_superuser)
def admin_analytics_view(request):
    """
    Fetches key metrics and detailed data for administrative analytics.
    """
    
    # --- 1. CORE COUNTS ---
    total_users = User.objects.all().count()
    total_policies = Policy.objects.all().count()

    # --- 2. RENEWAL TRACKING (New Metric) ---
    today = timezone.now().date()
    renewal_window = today + timezone.timedelta(days=30)
    
    # Policies expiring between today and the next 30 days
    policies_expiring_soon = Policy.objects.filter(
        status='ACTIVE',
        expiry_date__gte=today,
        expiry_date__lte=renewal_window
    ).count()

    # --- 3. CLAIM ANALYSIS ---
    claim_counts = Claim.objects.values('status').annotate(count=Count('status')).order_by('-count')
    claim_labels = [item['status'] for item in claim_counts]
    claim_data = [item['count'] for item in claim_counts]

    # --- 4. POLICY TYPE POPULARITY (Chart Data) ---
    policy_type_counts = Policy.objects.values('product__product_type').annotate(count=Count('product__product_type')).order_by('-count')
    
    policy_type_labels = [item['product__product_type'] for item in policy_type_counts]
    policy_type_data = [item['count'] for item in policy_type_counts]
    
    # Calculate percentages for display
    policy_percentages = []
    if total_policies > 0:
        for item in policy_type_counts:
            percentage = round((item['count'] / total_policies) * 100, 1)
            policy_percentages.append(f"{item['product__product_type']} ({percentage}%)")


    # --- 5. RECENT USERS ---
    last_week = timezone.now() - timezone.timedelta(days=7)
    recent_users = User.objects.filter(date_joined__gte=last_week).count()

    context = {
        'total_users': total_users,
        'total_policies': total_policies,
        'policies_expiring_soon': policies_expiring_soon, # New Metric
        'recent_users': recent_users,
        'policy_percentages': policy_percentages, # New Detailed List

        # Chart Data
        'claim_chart_labels': json.dumps(claim_labels),
        'claim_chart_data': json.dumps(claim_data),
        'policy_chart_labels': json.dumps(policy_type_labels),
        'policy_chart_data': json.dumps(policy_type_data),
    }
    return render(request, 'home/admin_analytics.html', context)

@login_required
def purchase_policy_view(request):
    """
    Handles the final stage of policy purchase, creating a new Policy record.
    """
    user = request.user
    
    if request.method == 'POST':
        form = PolicyPurchaseForm(request.POST) 
        if form.is_valid():
            product = form.cleaned_data['product']
            start_date = form.cleaned_data['start_date']
            
            # 1. Calculate Policy Details
            expiry_date = start_date + timezone.timedelta(days=365) # Assuming 1-year policy term
            premium_amount = product.base_premium + 1000 # Add a fixed processing fee for simplicity
            policy_number = f"GMS-{random.randint(100000, 999999)}" # Generate unique ID
            
            # 2. Create the Policy
            policy = form.save(commit=False)
            policy.user = user
            policy.policy_number = policy_number
            policy.premium_amount = premium_amount
            policy.expiry_date = expiry_date
            policy.status = 'ACTIVE' # Policy is active upon simulated purchase
            policy.save()
            
            # Redirect to the dashboard (with a real success message system needed in production)
            return redirect('dashboard')
    else:
        # For GET request, optionally pre-select a recommended product if passed in the URL
        initial_data = {}
        product_id = request.GET.get('product_id')
        if product_id:
            try:
                initial_data['product'] = InsuranceProduct.objects.get(id=product_id)
            except InsuranceProduct.DoesNotExist:
                pass
        
        form = PolicyPurchaseForm(initial=initial_data)

    context = {
        'form': form
    }
    return render(request, 'home/purchase_policy.html', context)