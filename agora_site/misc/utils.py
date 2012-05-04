"""
taken from

http://www.djangosnippets.org/snippets/377/
"""

from django.conf import settings
from django.core import mail as django_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import signals
from django.utils import simplejson as json
from django.views.generic import CreateView

import datetime
import pygeoip

class FormRequestMixin(object):
    '''
    Adds self.request to the form constructor arguments
    '''
    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        kwargs = super(FormRequestMixin, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

class RequestCreateView(FormRequestMixin, CreateView):
    pass

class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.

    deserialization_params added on 2011-01-09 to provide additional hints at deserialization time
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def __init__(self, name=None, json_type=None, deserialization_params=None, **kwargs):
        self.json_type = json_type
        self.deserialization_params = deserialization_params
        super(JSONField, self).__init__(name, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if self.json_type:
            if isinstance(value, self.json_type):
                return value

        if isinstance(value, dict) or isinstance(value, list):
            return value

        if value == "" or value == None:
            return None

        try:
            parsed_value = json.loads(value)
        except:
            raise Exception("not JSON")

        if self.json_type and parsed_value:
            parsed_value = self.json_type.fromJSONDict(parsed_value, **self.deserialization_params)

        return parsed_value

    # we should never look up by JSON field anyways.
    # def get_prep_lookup(self, lookup_type, value)

    def get_prep_value(self, value):
        """Convert our JSON object to a string before we save"""
        if isinstance(value, basestring):
            return value

        if value == None:
            return None

        if self.json_type and isinstance(value, self.json_type):
            the_dict = value.toJSONDict()
        else:
            the_dict = value

        return json.dumps(the_dict, cls=DjangoJSONEncoder)


    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


##
## for schema migration, we have to tell South about JSONField
## basically that it's the same as its parent class
##
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^agora_site\.misc\.utils\.JSONField"])

GEOIP = None

def geolocate_ip(ip_addr):
    '''
    Given an ip address, geolocates it, returning a tuple(latitude, longitude)
    '''
    global GEOIP

    try:
        if not GEOIP:
            GEOIP = pygeoip.GeoIP(settings.GEOIP_DB_PATH)
        data = GEOIP.record_by_addr(ip_addr)
        return [data["latitude"], data["longitude"]]
    except Exception, e:
        return [0, 0]

def get_protocol(request):
    '''
    Given the request object, returns either 'https' or 'http' appropiately
    '''
    if request.is_secure():
        return 'https'
    else:
        return 'http'
