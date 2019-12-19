from typing import Any, Dict

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from nestlist.models import (
    NstLocation,
    NstMetropolisMajor,
    NstNeighborhood,
    NstCombinedRegion,
    NstParkSystem,
    get_rotation,
)
from nestlist.utils import nested_dict, cardinal_direction_from_bearing


def serialize_alt_name(nest: NstLocation):
    return list(nest.alternate_name.exclude(hide_me=True).values("name"))


class TypeField(serializers.Field):
    def to_representation(self, value: Any) -> Any:
        return type(value)


class CoordinateSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)
        coords: Dict = {}
        at = instance.lat
        on = instance.lon
        if at is None or on is None:
            ret["coords"] = None
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
    typeNames = {
        NstMetropolisMajor: "Major City",
        NstNeighborhood: "Neighborhood or Suburb",
        NstLocation: "Park",
        NstParkSystem: "Park System",
        NstCombinedRegion: "Combined Region",
    }

    def to_representation(self, value: Any) -> Any:
        return self.typeNames.get(type(value), type(value))


class LinkedPlaceSerializer(serializers.Serializer):
    name = serializers.CharField(source="get_name")
    pk = serializers.IntegerField()
    api_url = serializers.URLField()
    web_url = serializers.URLField()


class CitySerializer(LinkedPlaceSerializer, CoordinateSerializer):
    pass


class NeighborhoodSerializer(LinkedPlaceSerializer, CoordinateSerializer):
    pass


class RegionSerializer(LinkedPlaceSerializer):
    pass


class ParkSysSerializer(LinkedPlaceSerializer):
    pass


class ParkSerializer(LinkedPlaceSerializer, CoordinateSerializer):
    address = serializers.CharField()
    private = serializers.BooleanField()

    def to_representation(self, instance: Any) -> Any:
        ret = super().to_representation(instance)

        # fancy stuff for names
        ret["other names"] = [instance.official_name] if instance.short_name else []
        for name in instance.alternate_name.exclude(hide_me=True):
            ret["other names"].append(name.name)

        # current resident
        if not hasattr(instance, "hide_sp"):
            try:
                rot = instance.rot
            except AttributeError:
                rot = get_rotation("t")
            try:
                rpt = instance.nstspecieslistarchive_set.get(rotation_num=rot)
                cr = {
                    "species": rpt.species_txt,
                    "dex": rpt.species_no,
                    "confirmation": bool(rpt.confirmation),
                }
            except ObjectDoesNotExist:
                cr = None
            ret["current resident"] = cr
        if not hasattr(instance, "hide_neighborhood") or not instance.hide_neighborhood:
            ret["neighborhood"] = (
                instance.neighborhood.pk if instance.neighborhood else None
            )
        if not hasattr(instance, "hide_ps") or not instance.hide_ps:
            ret["park system"] = (
                instance.park_system.pk if instance.park_system else None
            )
        return ret


class ParkDetailSerializer(ParkSerializer):
    permanent_species = serializers.CharField()
    osm_id = serializers.IntegerField()
    primary_silph_id = serializers.IntegerField()
    duplicated_to = ParkSerializer(source="duplicate_of")
    notes = serializers.CharField()

    def to_representation(self, instance: Any) -> Any:
        rep = super().to_representation(instance)
        if instance.neighborhood:
            rep["neighborhood"] = NeighborhoodSerializer().to_representation(
                instance.neighborhood
            )
            rep["city"] = CitySerializer().to_representation(
                instance.neighborhood.major_city
            )
        rep["prior entries"] = []
        for p in instance.all_old_duplicates():
            rep["prior entries"].append(ParkSerializer().to_representation(p))
        if rep["duplicated_to"]:
            chain = instance.duplicate_chain()
            rep["current entry"] = ParkSerializer().to_representation(chain[-1])
            rep["duplicate chain"] = []
            for p in chain:
                rep["duplicate chain"].append(ParkSerializer().to_representation(p))
        rep["species history"] = []
        for r in instance.nstspecieslistarchive_set.all():
            rep["species history"].append(
                ReportHistoricSerializer().to_representation(r)
            )
        return rep


class RotationSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> Any:
        return str(instance)


class ReportSerializer(serializers.Serializer):
    species = serializers.CharField(source="species_txt")
    dex = serializers.IntegerField(source="species_no")
    confirmation = serializers.BooleanField()


class ReportHistoricSerializer(ReportSerializer):
    rotation = RotationSerializer(source="rotation_num")


class StringSerializer(serializers.Serializer):
    def to_representation(self, instance: Any) -> Any:
        return instance.str
