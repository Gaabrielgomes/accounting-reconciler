from django import forms


class ReconcileForm(forms.Form):
    file = forms.FileField(label='Select a file')

class ManualAddForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    document = forms.FileField(label='Select a file')

class TextAddForm(forms.Form):
    text = forms.FileField(label="Choose the text file")