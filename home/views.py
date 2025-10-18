from django.shortcuts import render, redirect, get_object_or_404
from insurance.models import Policy, Claim, InsuranceProduct, Agent
from django.contrib.auth.decorators import login_required
from insurance.forms import ClaimForm
from django.http import Http404

def home_view(request):
    """
    Renders the main homepage for the website.
    """
    return render(request, 'home/homepage.html')
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
    Fetches all active agents to display in a directory.
    """
    # Simple directory listing for now, ordered by city
    agents = Agent.objects.filter(is_active=True).order_by('city', 'name')
    
    context = {
        'agents': agents
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
    Shows the detailed status and information for a single claim.
    """
    claim = get_object_or_404(Claim, id=claim_id)
    
    # Security Check: Ensure the user owns the policy related to this claim
    if claim.policy.user != request.user:
        raise Http404("You do not have permission to view this claim.")
        
    context = {
        'claim': claim,
        'policy': claim.policy, # Easily access policy details in the template
    }
    return render(request, 'home/claim_detail.html', context)