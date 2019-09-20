from nestlist.models import NstLocation
from rest_framework import serializers


class ParkSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NstLocation
        fields = ["official_name", "short_name", "neighborhood"]
