from django import forms


class ReconcileForm(forms.Form):
    file = forms.FileField(label='Select a file (.xlsx, .csv, .json, .txt)', widget=forms.ClearableFileInput(attrs={
        "class": "form-input",
        "accept": ".csv, .txt, .xlsx, .json"
    }))