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
            nav["bearing"]["initial"] = instance.bearing_initial
            nav["bearing"]["constant"] = instance.bearing_constant
            nav["distance"]["rhumb"] = instance.rhumb_len
            nav["distance"]["direct"] = instance.distance
            nav["general_direction"] = cardinal_direction_from_bearing(
                instance.bearing_constant
            )
            nav["loxodrome"]["distance"] = instance.rhumb_len
            nav["loxodrome"]["bearing"] = instance.bearing_constant
            nav["aviation"]["forward_azimuth"] = instance.bearing_initial
            nav["aviation"]["distance"] = instance.distance
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
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.neighborhood = (
            NeighborhoodSerializer()
            if not kwargs.get("summary")
            else serializers.CharField(read_only=True)
        )

    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)
        ret["other names"] = [instance.official_name] if instance.short_name else []
        for name in instance.alternate_name.exclude(hide_me=True):
            ret["other names"].append(name.name)
        return ret


class ReportSerializer(serializers.Serializer):
    park = ParkSerializer(source="nestid", summary=True)

    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)
        ret["species"] = instance.species_txt
        ret["dex"] = instance.species_no
        # ret["park"] = instance.nestid.get_name()
        # ret["neighborhood"] = instance.nestid.neighborhood.get_name()
        return ret
