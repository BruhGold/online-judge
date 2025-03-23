# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dmoj',
        'USER': 'dmoj',
        'PASSWORD': 'your_password_here',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Static and compression settings
STATIC_ROOT = "/home/ubuntu/dmojsite/site/static/"
COMPRESS_ROOT = STATIC_ROOT
