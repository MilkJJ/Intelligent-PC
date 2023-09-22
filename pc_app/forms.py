# forms.py

from django import forms
from .models import *
from django.contrib.auth.forms import PasswordChangeForm
#from star_ratings.views import StarRatingWidget

class CPUComparisonForm(forms.Form):
    cpu = forms.ModelChoiceField(queryset=CPU.objects.all(), label='Select a CPU for comparison', to_field_name='id')

class GPUComparisonForm(forms.Form):
    gpu = forms.ModelChoiceField(queryset=GPU.objects.all(), label='Select a GPU for comparison', to_field_name='id')

class MBoardComparisonForm(forms.Form):
    mboard = forms.ModelChoiceField(queryset=Motherboard.objects.all(), label='Select a Motherboard for comparison', to_field_name='id')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comments']
        # widgets = {
        #     'rating': StarRatingWidget(),
        # }