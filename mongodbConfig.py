import os
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from pymongo import MongoClient

MONGO_PORT = os.environ.get("MONGODB_PORT")
MONGO_HOST = os.environ.get("MONGODB_HOST")
MONGO_DB_NAME = os.environ.get("MONGODB_NAME")
MONGO_SESSIONS_COLLECTION = os.environ.get("MONGO_SESSIONS_COLLECTION")
MONGO_SESSIONS_TTL = getattr(
    settings, 'MONGO_SESSIONS_TTL', settings.SESSION_COOKIE_AGE
)

MONGO_CLIENT = MongoClient(
    host=MONGO_HOST,
    port=MONGO_PORT,
)
MONGO_CLIENT = MONGO_CLIENT[MONGO_DB_NAME]

try:
    MONGO_DB_VERSION = MONGO_CLIENT.connection.server_info()['version']
except TypeError:
    # for pymongo >= 3
    MONGO_DB_VERSION = MONGO_CLIENT.client.server_info()['version']

if not float('.'.join(MONGO_DB_VERSION.split('.')[:-1])) >= 2.2:
    raise ImproperlyConfigured()

DB_COLLECTION = MONGO_CLIENT[MONGO_SESSIONS_COLLECTION]

MONGO_SESSIONS_INDEXES = DB_COLLECTION.index_information()

if len(MONGO_SESSIONS_INDEXES) <= 1:
    DB_COLLECTION.ensure_index(
        'session_key',
        unique=True
    )

    DB_COLLECTION.ensure_index(
        'creation_date',
        expireAfterSeconds=MONGO_SESSIONS_TTL
    )

    MONGO_SESSIONS_INDEXES = DB_COLLECTION.index_information()

if int(MONGO_SESSIONS_INDEXES['creation_date_1']['expireAfterSeconds']) != int(MONGO_SESSIONS_TTL):
    DB_COLLECTION.drop_index('creation_date_1')
    DB_COLLECTION.ensure_index(
        'creation_date',
        expireAfterSeconds=MONGO_SESSIONS_TTL
    )

    MONGO_SESSIONS_INDEXES = DB_COLLECTION.index_information()
