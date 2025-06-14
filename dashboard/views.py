from django.shortcuts import render, redirect, get_object_or_404
from firms.models import Firm
from django.http import HttpResponseRedirect
from django.urls import reverse
import json as pyjson
from django.contrib.auth.decorators import login_required
from jsonschema import validate, ValidationError
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.

# Define a simple schema for the flow JSON
FLOW_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "message"],
                "properties": {
                    "id": {"type": "string"},
                    "message": {"type": "string"},
                    "next": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["pattern", "next"],
                                    "properties": {
                                        "pattern": {"type": "string"},  # regex pattern
                                        "next": {"type": "string"}      # next step ID
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
    },
    "required": ["steps"]
}


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
            # Validate JSON syntax
            flow_data = pyjson.loads(json_text)
            # Validate JSON against schema
            validate(instance=flow_data, schema=FLOW_SCHEMA)
            firm.flow = flow_data
            firm.save()
            return HttpResponseRedirect(reverse('dashboard_firm_list'))
        except pyjson.JSONDecodeError as e:
            error = f"Invalid JSON syntax: {e}"
        except ValidationError as e:
            error = f"Invalid flow structure: {e}"
    flow_json = pyjson.dumps(firm.flow, indent=2) if firm.flow else pyjson.dumps({"steps": []}, indent=2)
    return render(request, 'dashboard/edit_firm_flow.html', {'firm': firm, 'flow_json': flow_json, 'error': error})

def dashboard_root(request):
    if request.user.is_authenticated:
        return redirect('dashboard_firm_list')
    else:
        return redirect('dashboard_login')

class DashboardLoginView(LoginView):
    template_name = 'dashboard/login.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse('dashboard_firm_list')
