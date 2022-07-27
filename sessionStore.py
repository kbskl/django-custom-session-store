from datetime import timedelta
from enum import Enum

import redis
from django.utils.encoding import force_str as force_unicode
from django.contrib.sessions.backends.base import SessionBase, CreateError
from django.utils import timezone
from mongodbConfig import DB_COLLECTION, MONGO_SESSIONS_TTL
from redisConfig import *


class StoragePlace(Enum):
    Redis = "Redis"
    MongoDB = "MongoDB"


class SessionStore(SessionBase):

    def __init__(self, session_key=None):
        super(SessionStore, self).__init__(session_key)
        try:
            self.server = redis.Redis(host=SESSION_REDIS_HOST, port=SESSION_REDIS_PORT, db=SESSION_REDIS_DB, password="22032024",
                                      socket_timeout=SESSION_REDIS_SOCKET_TIMEOUT,
                                      retry_on_timeout=SESSION_REDIS_RETRY_ON_TIMEOUT)
            self.server.ping()
            self.storage_place = StoragePlace.Redis.value
        except Exception as e:
            self.storage_place = StoragePlace.MongoDB.value
            self.server = DB_COLLECTION

    def load(self):
        if self.storage_place == StoragePlace.Redis.value:
            try:
                session_data = self.server.get(
                    self.__redis_get_real_stored_key(self._get_or_create_session_key())
                )
                return self.decode(force_unicode(session_data))
            except:
                self._session_key = None
                return {}
        else:
            mongo_session = self.server.find_one({
                'session_key': self._get_or_create_session_key(),
                'creation_date': {
                    '$gt': self.__mongodb_get_expiration_date()
                }
            })
            if not mongo_session is None:
                return self.decode(force_unicode(mongo_session['session_data']))
            else:
                self._session_key = None
                return {}

    def exists(self, session_key):
        if self.storage_place == StoragePlace.Redis.value:
            return self.server.exists(self.__redis_get_real_stored_key(session_key))
        else:
            session = self.server.find_one({
                'session_key': session_key,
            })
            if session is None:
                return False
            else:
                if session['creation_date'] <= self.__mongodb_get_expiration_date():
                    self.delete(session_key)
                    return self.exists(session_key)
                return True

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if self.session_key is None:
            return self.create()
        if must_create and self.exists(self.session_key):
            raise CreateError

        if self.storage_place == StoragePlace.Redis.value:
            data = self.encode(self._get_session(no_load=must_create))
            self.server.setex(
                self.__redis_get_real_stored_key(self._get_or_create_session_key()),
                self.__mongodb_get_expiry_age(),
                data
            )
        else:
            session = {
                'session_key': self.session_key,
                'session_data': self.encode(
                    self._get_session(no_load=must_create)
                ),
                'creation_date': timezone.now()
            }
            self.server.update(
                {'session_key': self.session_key},
                {'$set': session},
                upsert=True
            )

    def delete(self, session_key=None):
        if session_key is None:
            if self._session_key is None:
                return
            session_key = self.session_key
        if self.storage_place == StoragePlace.Redis.value:
            try:
                self.server.delete(self.__redis_get_real_stored_key(session_key))
            except:
                pass
        else:
            self.server.remove({'session_key': session_key})

    @classmethod
    def clear_expired(cls):
        pass

    def __redis_get_real_stored_key(self, session_key):
        prefix = SESSION_REDIS_PREFIX
        if not prefix:
            return session_key
        return ':'.join([prefix, session_key])

    def __mongodb_get_expiry_age(self):
        return MONGO_SESSIONS_TTL

    def __mongodb_get_expiration_date(self):
        return timezone.now() - timedelta(seconds=self.__mongodb_get_expiry_age())
