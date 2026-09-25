import base64
import io
import re

import pyotp
import qrcode
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView

from auditing import actions
from auditing.services import record_audit_event
from authentication.services import blacklist_user_tokens
from .forms import (
    AccountEditForm,
    EmailAuthenticationForm,
    InviteAcceptForm,
    MFASetupForm,
    MFAVerifyForm,
)
from .models import Account, Invite, MFASetup, RecoveryCode
from .rate_limit import (
    is_invite_rate_limited,
    is_login_rate_limited,
    is_mfa_rate_limited,
    is_mfa_setup_rate_limited,
)


class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        record_audit_event(
            action=actions.LOGIN_SUCCESS,
            user=user,
            resource_type='User',
            resource_id=user.pk,
            description='Login realizado.',
            request=self.request,
        )
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        record_audit_event(
            action=actions.LOGIN_FAILURE,
            user=None,
            resource_type='User',
            resource_id='',
            description='Tentativa de login invalida.',
            status='failure',
            request=self.request,
        )
        return response

    def post(self, request, *args, **kwargs):
        if is_login_rate_limited(request, request.POST.get('email', '')):
            form = self.get_form()
            form.add_error(None, 'Muitas tentativas. Tente novamente mais tarde.')
            response = self.form_invalid(form)
            response.status_code = 429
            return response

        return super().post(request, *args, **kwargs)


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'account_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.select_related('user').filter(user=self.request.user)


def invite_accept(request, token):
    invite = get_object_or_404(Invite, token_hash=Invite.hash_token(token))
    if not invite.is_valid:
        return render(request, 'accounts/invite_invalid.html', status=410)

    if request.method == 'POST':
        if is_invite_rate_limited(request):
            return HttpResponse('Muitas tentativas. Tente novamente mais tarde.', status=429)

        form = InviteAcceptForm(request.POST, invite_email=invite.email)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data['name'],
                    email=invite.email,
                    password=form.cleaned_data['password'],
                )
                user.is_staff = invite.is_superuser
                user.is_superuser = invite.is_superuser
                user.save(update_fields=['is_staff', 'is_superuser'])

                account, _ = Account.objects.get_or_create(user=user)
                account.name = form.cleaned_data['name']
                account.save(update_fields=['name', 'updated_at'])

                invite.used_at = timezone.now()
                invite.save(update_fields=['used_at'])

            login(
                request,
                user,
                backend='django.contrib.auth.backends.ModelBackend',
            )
            return redirect('mfa_setup')
    else:
        form = InviteAcceptForm(invite_email=invite.email)

    return render(request, 'accounts/invite_accept.html', {
        'form': form,
        'invite': invite,
    })


@login_required(login_url='login')
def account_edit(request):
    account = get_object_or_404(Account, user=request.user)

    if request.method == 'POST':
        form = AccountEditForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('account_list')
    else:
        form = AccountEditForm(instance=account, initial={
            'name': account.name,
            'username': account.user.username,
            'email': account.user.email,
        })

    return render(request, 'account_edit.html', {'form': form, 'account': account})


@login_required(login_url='login')
def mfa_setup(request):
    setup, _ = MFASetup.objects.get_or_create(user=request.user)
    if setup.confirmed_at:
        return redirect('mfa_verify')

    if not setup.secret:
        setup.secret = pyotp.random_base32()
        setup.save(update_fields=['secret', 'updated_at'])

    if request.method == 'POST':
        if is_mfa_setup_rate_limited(request, request.user):
            return render(
                request,
                'accounts/mfa_setup.html',
                {
                    'form': MFASetupForm(),
                    'qr_code': None,
                    'secret': setup.secret,
                    'setup_completed': False,
                    'error_message': 'Muitas tentativas. Tente novamente mais tarde.',
                },
                status=429,
            )

        form = MFASetupForm(request.POST)
        if form.is_valid():
            totp = pyotp.TOTP(setup.secret)
            if totp.verify(form.cleaned_data['code'].strip(), valid_window=1):
                setup.confirmed_at = timezone.now()
                setup.save(update_fields=['confirmed_at', 'updated_at'])

                RecoveryCode.objects.filter(user=request.user, used_at__isnull=True).delete()
                recovery_codes = []
                for _ in range(8):
                    code = RecoveryCode.generate_code()
                    RecoveryCode.objects.create(
                        user=request.user,
                        code_hash=RecoveryCode.hash_code(code),
                    )
                    recovery_codes.append(code)

                request.session['mfa_verified'] = True
                request.session['mfa_verified_user_id'] = request.user.pk
                record_audit_event(
                    action=actions.MFA_SETUP_SUCCESS,
                    user=request.user,
                    resource_type='MFASetup',
                    resource_id=setup.pk,
                    description='MFA TOTP ativado.',
                    request=request,
                )
                return render(request, 'accounts/mfa_setup.html', {
                    'recovery_codes': recovery_codes,
                    'setup_completed': True,
                })

            form.add_error('code', 'Codigo invalido. Tente novamente.')
    else:
        form = MFASetupForm()

    provisioning_uri = pyotp.TOTP(setup.secret).provisioning_uri(
        name=request.user.username,
        issuer_name='GAW Finance',
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    qr_code = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'accounts/mfa_setup.html', {
        'form': form,
        'qr_code': qr_code,
        'secret': setup.secret,
        'setup_completed': False,
    })


@login_required(login_url='login')
def mfa_verify(request):
    setup = MFASetup.objects.filter(
        user=request.user,
        confirmed_at__isnull=False,
    ).first()
    if not setup:
        return redirect('mfa_setup')

    if request.session.get('mfa_verified') and request.session.get('mfa_verified_user_id') == request.user.pk:
        return redirect('/')

    if request.method == 'POST':
        if is_mfa_rate_limited(request, request.user):
            return render(
                request,
                'accounts/mfa_verify.html',
                {
                    'form': MFAVerifyForm(),
                    'error_message': 'Muitas tentativas. Tente novamente mais tarde.',
                },
                status=429,
            )

        form = MFAVerifyForm(request.POST)
        if form.is_valid():
            code = re.sub(r'[^A-Za-z0-9]', '', form.cleaned_data['code']).upper()
            verified = False

            if len(code) == 6 and code.isdigit():
                totp = pyotp.TOTP(setup.secret)
                verified = totp.verify(code, valid_window=1)

            if not verified:
                recovery_code = RecoveryCode.objects.filter(
                    user=request.user,
                    code_hash=RecoveryCode.hash_code(code),
                    used_at__isnull=True,
                ).first()
                if recovery_code:
                    recovery_code.used_at = timezone.now()
                    recovery_code.save(update_fields=['used_at'])
                    verified = True

            if verified:
                request.session['mfa_verified'] = True
                request.session['mfa_verified_user_id'] = request.user.pk
                record_audit_event(
                    action=actions.MFA_VERIFY_SUCCESS,
                    user=request.user,
                    resource_type='MFASetup',
                    resource_id=setup.pk,
                    description='MFA verificado.',
                    request=request,
                )
                return redirect('/')
            record_audit_event(
                action=actions.MFA_VERIFY_FAILURE,
                user=request.user,
                resource_type='MFASetup',
                resource_id=setup.pk,
                description='Tentativa de verificacao MFA invalida.',
                status='failure',
                request=request,
            )
            form.add_error('code', 'Codigo invalido. Tente novamente.')
    else:
        form = MFAVerifyForm()

    return render(request, 'accounts/mfa_verify.html', {'form': form})


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        blacklist_user_tokens(self.request.user)
        record_audit_event(
            action=actions.PASSWORD_CHANGE_SUCCESS,
            user=self.request.user,
            resource_type='User',
            resource_id=self.request.user.pk,
            description='Senha alterada.',
            request=self.request,
        )
        return response


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
