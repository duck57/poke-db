from nestlist.models import (
    NstLocation,
    NstMetropolisMajor,
    NstNeighborhood,
    NstCombinedRegion,
)
from rest_framework import serializers


class ParkSerializer(serializers.ModelSerializer):
    neighborhood_name = serializers.ReadOnlyField(source="neighborhood.name")
    neighborhood_id = serializers.ReadOnlyField(source="neighborhood")
    # alt_names = serializers.ListSerializer(source="nstaltname_set")

    class Meta:
        model = NstLocation
        fields = [
            "nestID",
            "official_name",
            "short_name",
            "neighborhood_id",
            "neighborhood_name",
            "resident_history",
            "pk",
            "address",
            "private",
            "notes",
            # "alt_names",
        ]


class CitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NstMetropolisMajor


class NeighborhoodSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NstNeighborhood


class RegionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NstCombinedRegion
