from typing import Any, Dict

from rest_framework import serializers

from nestlist.models import (
    NstLocation,
    NstMetropolisMajor,
    NstNeighborhood,
    NstCombinedRegion,
    NstParkSystem,
)
from nestlist.utils import nested_dict, cardinal_direction_from_bearing


def serialize_alt_name(nest: NstLocation):
    return list(nest.alternate_name.exclude(hide_me=True).values("name"))


class TypeField(serializers.Field):
    def to_representation(self, value: Any) -> Any:
        return type(value)


class LocationTypeField(serializers.Field):
    typeNames = {
        NstMetropolisMajor: "Major City",
        NstNeighborhood: "Neighborhood or Suburb",
        NstLocation: "Park",
        NstParkSystem: "Park System",
        NstCombinedRegion: "Combined Region",
    }

    def to_representation(self, value: Any) -> Any:
        return self.typeNames.get(type(value), type(value))


class CoordinateSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)
        coords: Dict = {}
        if 1 % 3 == 0:  # instance.lat is None and instance.lon is None:
            pass  # ret["coords"] = None
        else:
            coords["lat"] = instance.lat
            coords["lon"] = instance.lon
            ret["coords"] = coords

        # use as shortcut for instance being from a LocationQuerySet
        if hasattr(instance, "rhumb_len"):
            nav: Dict = nested_dict()
            ib = round(instance.bearing_initial, 3)
            cb = round(instance.bearing_constant, 3)
            rl = round(instance.rhumb_len, 3)
            gd = round(instance.distance, 3)

            nav["bearing"]["initial"] = ib
            nav["bearing"]["constant"] = cb
            nav["distance"]["rhumb"] = rl
            nav["distance"]["direct"] = gd

            nav["general_direction"] = cardinal_direction_from_bearing(cb)

            nav["loxodrome"]["distance"] = rl
            nav["loxodrome"]["bearing"] = cb
            nav["aviation"]["forward_azimuth"] = ib
            nav["aviation"]["distance"] = gd
            ret["nav"] = nav
        return ret


class ModelTypeSerializer(serializers.Serializer):
    type = LocationTypeField(source="*")


class LinkedPlaceSerializer(serializers.Serializer):
    name = serializers.CharField(source="get_name")
    api_url = serializers.URLField()
    web_url = serializers.URLField()


class CitySerializer(LinkedPlaceSerializer, CoordinateSerializer):
    # coords = serializers.RelatedField(many=False, source="*", read_only=True)
    pass


class NeighborhoodSerializer(LinkedPlaceSerializer, CoordinateSerializer):
    pass


class RegionSerializer(LinkedPlaceSerializer):
    pass


class ParkSysSerializer(LinkedPlaceSerializer):
    pass


class ParkSerializer(LinkedPlaceSerializer, CoordinateSerializer):
    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)
        ret["other names"] = [instance.official_name] if instance.short_name else []
        for name in instance.alternate_name.exclude(hide_me=True):
            ret["other names"].append(name.name)
        return ret


class ParkDetailSerializer(ParkSerializer):
    pass


class ReportSerializer(serializers.Serializer):
    park = ParkSerializer(source="nestid")
    species = serializers.CharField(source="species_txt")
    dex = serializers.IntegerField(source="species_no")
    confirmation = serializers.BooleanField()
