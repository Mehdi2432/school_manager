# school_manager/settings.py
import os

# مسیر پایه پروژه
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# کلید امنیتی (این رو یه مقدار امن جایگزین کن)
SECRET_KEY = 'your-secret-key-here'

# حالت دیباگ
DEBUG = True

# میزبان‌های مجاز
ALLOWED_HOSTS = []

# اپلیکیشن‌های نصب‌شده
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'teacher',
    'school_admin',
    'parent',
]

# میدلورها
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# تنظیمات URL
ROOT_URLCONF = 'school_manager.urls'

# تنظیمات تمپلیت
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# برنامه WSGI
WSGI_APPLICATION = 'school_manager.wsgi.application'

# دیتابیس
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# تنظیمات زبان و زمان
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# تنظیمات استاتیک
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'teacher/static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ریدایرکت بعد از خروج
LOGOUT_REDIRECT_URL = '/teacher/login/'

# تنظیمات سشن
SESSION_COOKIE_AGE = 28800  # 8 ساعت (8 * 60 * 60)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # با بستن مرورگر منقضی می‌شه

# تنظیمات لاگ
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '__name__': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}