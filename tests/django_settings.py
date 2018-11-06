DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'easy_thumbnails',
]

SECRET_KEY = 'notsosecret'
DEFAULT_INDEX_TABLESPACE = ''
