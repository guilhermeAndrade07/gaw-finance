from django import forms
from django.contrib.auth.models import User


class AccountCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    confirm_password = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        if not name:
            raise forms.ValidationError('Informe um nome para a conta.')

        if User.objects.filter(username__iexact=name).exists():
            raise forms.ValidationError('Ja existe uma conta com este nome.')

        return name

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ja existe uma conta com este email.')

        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'A confirmacao de senha nao confere.')

        return cleaned_data

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
        )
