from django.db import models

# Create your models here.


class TypeEffectiveness(models.Model):
    otype = models.ForeignKey('Type', models.DO_NOTHING, db_column='otype', related_name='offensive_type')
    relation = models.ForeignKey('TypeEffectivenessRating', models.DO_NOTHING, db_column='relation', blank=True, null=True)
    dtype = models.ForeignKey('Type', models.DO_NOTHING, db_column='dtype', related_name='defensive_type')
    id = models.AutoField(db_column='django_id', primary_key=True)

    class Meta:
        managed = False
        db_table = 'type_effectiveness'
        unique_together = (('otype', 'dtype'),)

    def __str__(self):
        return f'{self.otype.name} {self.relation.description} against {self.dtype.name}'

    search_fields = ['otype', 'relation', 'dtype']


class TypeEffectivenessRating(models.Model):
    description = models.CharField(max_length=23)
    dmg_multiplier = models.FloatField()
    pogodamage = models.FloatField(db_column='PoGoDamage')
    oldpogodamage = models.FloatField(db_column='oldPoGoDamage')

    class Meta:
        managed = False
        db_table = 'type_effectiveness_ratings'

    def __str__(self):
        return self.description

    def __cmp__(self, other):
        if self.dmg_multiplier == other.dmg_multiplier:
            return 0
        if self.dmg_multiplier > other.dmg_multiplier:
            return 1
        return -1


class Type(models.Model):
    name = models.CharField(unique=True, max_length=55)
    glitch = models.BooleanField(default=True)
    note = models.CharField(max_length=111, blank=True, null=True)
    weather_boost = models.ForeignKey('GoWeather', models.DO_NOTHING, db_column='weather_boost', blank=True, null=True)
    emoji = models.CharField(max_length=8, blank=True, null=True)
    id = models.IntegerField(primary_key=True, db_column='id')
    AtkEffectiveness = models.ManyToManyField(
        'Type',
        symmetrical=False,
        through='TypeEffectiveness',
        through_fields=('otype', 'dtype'),
        related_name='attack_effects'
    )
    DefEffectiveness = models.ManyToManyField(
        'Type',
        symmetrical=False,
        through='TypeEffectiveness',
        through_fields=('dtype', 'otype'),
        related_name='defense_effects'
    )

    class Meta:
        managed = False
        db_table = 'type_list'

    def __str__(self):
        return self.name

    def matches(self, q):
        """
        :param q: query to search
        :return: if q matches either the type's ID or name
        """
        return self.id == q or self.name.lower() == str(q).lower().strip()


class GoWeather(models.Model):
    name = models.CharField(db_column='Name', max_length=20)
    emoji = models.CharField(db_column='Emoji', max_length=8, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'GO_weather'

    def __str__(self):
        return self.emoji
