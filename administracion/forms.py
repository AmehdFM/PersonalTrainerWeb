from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ('nombre', 'apellido', 'correo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Custom styles for all fields including password fields from UserCreationForm
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition',
                'placeholder': field.label
            })

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition',
        'placeholder': 'tu@ejemplo.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition',
        'placeholder': '••••••••'
    }))
