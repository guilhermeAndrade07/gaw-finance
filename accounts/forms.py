from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Account


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

        if password:
            try:
                validate_password(password, user=User(
                    username=cleaned_data.get('name', ''),
                    email=cleaned_data.get('email', ''),
                ))
            except forms.ValidationError as e:
                self.add_error('password', e)

        return cleaned_data

    def save(self):
        return User.objects.create_user(
            username=self.cleaned_data['name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
        )


class AccountEditForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    username = forms.CharField(
        max_length=150,
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Informe um nome.')
        if Account.objects.exclude(pk=self.instance.pk if self.instance else None).filter(name__iexact=name).exists():
            raise forms.ValidationError('Ja existe uma conta com este nome.')
        return name

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError('Informe um usuario.')
        qs = User.objects.exclude(pk=self.instance.user.pk if self.instance else None)
        if qs.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ja existe um usuario com este nome.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.exclude(pk=self.instance.user.pk if self.instance else None)
        if qs.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ja existe uma conta com este email.')
        return email

    def save(self):
        account = self.instance
        account.name = self.cleaned_data['name']
        account.user.username = self.cleaned_data['username']
        account.user.email = self.cleaned_data['email']
        account.user.save(update_fields=['username', 'email'])
        account.save(update_fields=['name', 'updated_at'])
        return account
