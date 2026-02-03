from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Claim, ClaimStep
from .forms import ClaimForm
from .utils import send_claim_notification

@login_required
def file_claim_view(request):
    user = request.user
    
    if request.method == 'POST':
        # request.FILES is CRITICAL for images
        form = ClaimForm(request.POST, request.FILES, user=user) 
        
        if form.is_valid():
            claim = form.save(commit=False)
            claim.status = 'FILED'
            claim.save()
            
            # Send Notification
            send_claim_notification(user, claim)
            
            return redirect('dashboard') # Redirect to dashboard after success
    else:
        form = ClaimForm(user=user)

    return render(request, 'claims/file_claim.html', {'form': form})

@login_required
def claim_detail_view(request, claim_id):
    claim = get_object_or_404(Claim, id=claim_id)
    
    # Security: Ensure user owns this claim
    if claim.policy.user != request.user:
        return redirect('dashboard')
        
    # Get guidance steps (e.g., "Step 1: Surveyor Visit")
    guidance = ClaimStep.objects.filter(product_type=claim.policy.product.product_type)
    
    return render(request, 'claims/claim_detail.html', {
        'claim': claim,
        'guidance_steps': guidance
    })