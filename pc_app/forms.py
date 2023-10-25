# forms.py

from django import forms
from .models import *
from django.contrib.auth.forms import PasswordChangeForm

# class CPUComparisonForm(forms.Form):
#     cpu = forms.ModelChoiceField(queryset=CPU.objects.all(), label='Select a CPU for comparison', to_field_name='id')

# class GPUComparisonForm(forms.Form):
#     gpu = forms.ModelChoiceField(queryset=GPU.objects.all(), label='Select a GPU for comparison', to_field_name='id')

# class MBoardComparisonForm(forms.Form):
#     mboard = forms.ModelChoiceField(queryset=Motherboard.objects.all(), label='Select a Motherboard for comparison', to_field_name='id')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']

class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(max_length=20, required=False)

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'feedbacks']

class CPUPivotTableForm(forms.Form):
    cpuRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'cpu_ratingInput'})
    )

class GPUPivotTableForm(forms.Form):
    gpuRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'gpu_ratingInput'})
    )

class RAMPivotTableForm(forms.Form):
    ramRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'ram_ratingInput'})
    )

class MotherboardPivotTableForm(forms.Form):
    mboardRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'mboard_ratingInput'})
    )

class PSUPivotTableForm(forms.Form):
    psuRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'psu_ratingInput'})
    )

class StoragePivotTableForm(forms.Form):
    storageRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'storage_ratingInput'})
    )

class PCasePivotTableForm(forms.Form):
    caseRating = forms.ChoiceField(
        label="Select Rating",
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        widget=forms.Select(attrs={'id': 'case_ratingInput'})
    )