# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "*g23px2la-)2@u)w(&k54lg=mndcq+hc00t#@b63wbb8g-f9hh"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pogo",
        "USER": "root",
        "PASSWORD": "_n0t@te$tPa$war",
        "HOST": "localhost",
        "PORT": "",
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

SYSTEM_BOT_USER = 7
