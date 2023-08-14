# forms.py

from django import forms
from .models import CPU, GPU, Profile

class CPUComparisonForm(forms.Form):
    cpu = forms.ModelChoiceField(queryset=CPU.objects.all(), label='Select a CPU for comparison', to_field_name='id')

class GPUComparisonForm(forms.Form):
    gpu = forms.ModelChoiceField(queryset=GPU.objects.all(), label='Select a GPU for comparison', to_field_name='id')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']