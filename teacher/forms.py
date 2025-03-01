# school_manager/teacher/forms.py
from django import forms

class TeacherLoginForm(forms.Form):
    username = forms.CharField(label='نام کاربری', max_length=100)
    password = forms.CharField(label='رمز عبور', widget=forms.PasswordInput)