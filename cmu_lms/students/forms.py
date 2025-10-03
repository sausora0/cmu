from django import forms

class JoinClassForm(forms.Form):
    code = forms.CharField(max_length=6, label="Enter Class Code")
