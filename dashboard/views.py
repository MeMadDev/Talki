from django.shortcuts import render, redirect
from firms.models import Firm
from django.http import HttpResponseRedirect
from django.urls import reverse
import json as pyjson
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def firm_list(request):
    firms = Firm.objects.all()
    return render(request, 'dashboard/firm_list.html', {'firms': firms})

@login_required
def edit_firm_flow(request, firm_id):
    firm = Firm.objects.get(id=firm_id)
    error = None
    if request.method == 'POST':
        json_text = request.POST.get('flow_json', '')
        try:
            # Validate JSON
            flow_data = pyjson.loads(json_text)
            firm.flow = flow_data
            firm.save()
            return HttpResponseRedirect(reverse('dashboard_firm_list'))
        except Exception as e:
            error = f"Invalid JSON: {e}"
    flow_json = pyjson.dumps(firm.flow, indent=2) if firm.flow else '{}'
    return render(request, 'dashboard/edit_firm_flow.html', {'firm': firm, 'flow_json': flow_json, 'error': error})

def dashboard_root(request):
    if request.user.is_authenticated:
        return redirect('dashboard_firm_list')
    else:
        return redirect('dashboard_login')
