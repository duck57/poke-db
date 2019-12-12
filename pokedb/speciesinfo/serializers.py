from typing import Any, Dict

from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from speciesinfo.models import Pokemon, Type


class BasicPokemonSerializer(serializers.ModelSerializer):
    pass


class DetailPokemonSerializer(BasicPokemonSerializer):
    pass


class TypeSerializer(serializers.ModelSerializer):
    pass
