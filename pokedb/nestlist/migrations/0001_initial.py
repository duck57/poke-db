# Generated by Django 2.2 on 2019-01-16 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Abilities",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(db_column="Name", max_length=50)),
                ("effect", models.CharField(db_column="Effect", max_length=333)),
                (
                    "note",
                    models.CharField(
                        blank=True, db_column="Note", max_length=99, null=True
                    ),
                ),
            ],
            options={"db_table": "Abilities", "managed": False},
        ),
        migrations.CreateModel(
            name="Biomes",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=30)),
                (
                    "pogo",
                    models.PositiveIntegerField(
                        blank=True, db_column="PoGo", null=True
                    ),
                ),
            ],
            options={"db_table": "Biomes", "managed": False},
        ),
        migrations.CreateModel(
            name="BodyPlans",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("description", models.CharField(blank=True, max_length=50, null=True)),
                ("notes", models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={"db_table": "body_plans", "managed": False},
        ),
        migrations.CreateModel(
            name="Egggroups",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20)),
                ("notes", models.CharField(blank=True, max_length=199, null=True)),
                (
                    "stadium2name",
                    models.CharField(
                        blank=True, db_column="Stadium2name", max_length=20, null=True
                    ),
                ),
            ],
            options={"db_table": "EggGroups", "managed": False},
        ),
        migrations.CreateModel(
            name="Generations",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("region", models.CharField(db_column="Region", max_length=12)),
                (
                    "games",
                    models.CharField(
                        blank=True, db_column="Games", max_length=111, null=True
                    ),
                ),
                (
                    "note",
                    models.CharField(
                        blank=True, db_column="Note", max_length=111, null=True
                    ),
                ),
            ],
            options={"db_table": "generations", "managed": False},
        ),
        migrations.CreateModel(
            name="GoIvFloors",
            fields=[
                ("min", models.AutoField(primary_key=True, serialize=False)),
                ("comment", models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={"db_table": "GO_IV_floors", "managed": False},
        ),
        migrations.CreateModel(
            name="GoPowerupLevel",
            fields=[
                (
                    "level",
                    models.DecimalField(
                        db_column="Level",
                        decimal_places=1,
                        max_digits=3,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "cp_multiplier",
                    models.DecimalField(
                        db_column="CP_Multiplier", decimal_places=10, max_digits=11
                    ),
                ),
                ("wild", models.CharField(db_column="Wild", max_length=1)),
                ("total_candy", models.IntegerField()),
                ("total_dust", models.IntegerField()),
                ("next_level_candy", models.IntegerField(blank=True, null=True)),
                ("next_level_dust", models.IntegerField(blank=True, null=True)),
            ],
            options={"db_table": "GO_powerup_level", "managed": False},
        ),
        migrations.CreateModel(
            name="GoRaidHp",
            fields=[
                ("level", models.AutoField(primary_key=True, serialize=False)),
                ("hp", models.PositiveIntegerField(db_column="HP")),
                ("time", models.PositiveIntegerField()),
                ("notes", models.CharField(blank=True, max_length=222, null=True)),
                ("min_dps_theory", models.FloatField(blank=True, null=True)),
                ("min_dps_realistic", models.FloatField(blank=True, null=True)),
                ("min_dps_rejoins", models.FloatField(blank=True, null=True)),
            ],
            options={"db_table": "go_raid_hp", "managed": False},
        ),
        migrations.CreateModel(
            name="GoTeams",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=11, null=True, unique=True),
                ),
                ("color", models.CharField(blank=True, max_length=11, null=True)),
                ("color_id", models.IntegerField(blank=True, null=True)),
            ],
            options={"db_table": "GO_teams", "managed": False},
        ),
        migrations.CreateModel(
            name="GoTrainerLevel",
            fields=[
                (
                    "level",
                    models.IntegerField(
                        db_column="Level", primary_key=True, serialize=False
                    ),
                ),
                ("xp_required", models.IntegerField(db_column="XP_required")),
                ("total_xp", models.IntegerField(db_column="Total_XP", unique=True)),
                (
                    "unlocked_items",
                    models.CharField(
                        blank=True, db_column="Unlocked_items", max_length=22, null=True
                    ),
                ),
                (
                    "ball",
                    models.CharField(
                        blank=True, db_column="Ball", max_length=5, null=True
                    ),
                ),
                (
                    "balls",
                    models.IntegerField(blank=True, db_column="Balls", null=True),
                ),
                (
                    "potion",
                    models.CharField(
                        blank=True, db_column="Potion", max_length=6, null=True
                    ),
                ),
                (
                    "potions",
                    models.IntegerField(blank=True, db_column="Potions", null=True),
                ),
                (
                    "max",
                    models.CharField(
                        blank=True, db_column="Max", max_length=2, null=True
                    ),
                ),
                (
                    "revives",
                    models.IntegerField(blank=True, db_column="Revives", null=True),
                ),
                (
                    "razz_berries",
                    models.IntegerField(
                        blank=True, db_column="Razz_Berries", null=True
                    ),
                ),
                (
                    "incense",
                    models.IntegerField(blank=True, db_column="Incense", null=True),
                ),
                (
                    "lucky_eggs",
                    models.IntegerField(blank=True, db_column="Lucky_Eggs", null=True),
                ),
                (
                    "incubators",
                    models.IntegerField(blank=True, db_column="Incubators", null=True),
                ),
                (
                    "lure_modules",
                    models.IntegerField(
                        blank=True, db_column="Lure_Modules", null=True
                    ),
                ),
                (
                    "log_xp",
                    models.DecimalField(
                        blank=True,
                        db_column="log_XP",
                        decimal_places=3,
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "log_total_xp",
                    models.DecimalField(
                        blank=True,
                        db_column="log_total_XP",
                        decimal_places=3,
                        max_digits=4,
                        null=True,
                    ),
                ),
                (
                    "max_xp",
                    models.IntegerField(blank=True, db_column="max_XP", null=True),
                ),
                (
                    "nanab_berries",
                    models.IntegerField(
                        blank=True, db_column="Nanab_Berries", null=True
                    ),
                ),
                (
                    "pinap_berries",
                    models.IntegerField(
                        blank=True, db_column="Pinap_Berries", null=True
                    ),
                ),
            ],
            options={"db_table": "GO_trainer_level", "managed": False},
        ),
        migrations.CreateModel(
            name="GoWeather",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(db_column="Name", max_length=20)),
                (
                    "emoji",
                    models.CharField(
                        blank=True, db_column="Emoji", max_length=8, null=True
                    ),
                ),
            ],
            options={"db_table": "GO_weather", "managed": False},
        ),
        migrations.CreateModel(
            name="NstAdminEmail",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=90, null=True)),
                ("shortname", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "e_mail",
                    models.CharField(
                        blank=True, db_column="e-mail", max_length=90, null=True
                    ),
                ),
            ],
            options={"db_table": "NST_admin_email", "managed": False},
        ),
        migrations.CreateModel(
            name="NstAltNames",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=222)),
                ("hideme", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"db_table": "NST_alt_names", "managed": False},
        ),
        migrations.CreateModel(
            name="NstCombinedRegions",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=222)),
            ],
            options={"db_table": "NST_combined_regions", "managed": False},
        ),
        migrations.CreateModel(
            name="NstLocations",
            fields=[
                (
                    "nestid",
                    models.AutoField(
                        db_column="nest_id", primary_key=True, serialize=False
                    ),
                ),
                ("official_name", models.CharField(max_length=222)),
                ("short_name", models.CharField(blank=True, max_length=222, null=True)),
                ("address", models.CharField(blank=True, max_length=234, null=True)),
                ("notes", models.CharField(blank=True, max_length=234, null=True)),
                ("private", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "permanent_species",
                    models.CharField(blank=True, max_length=111, null=True),
                ),
                ("lat", models.FloatField(blank=True, null=True)),
                ("lon", models.FloatField(blank=True, null=True)),
                ("size", models.IntegerField(blank=True, null=True)),
                ("density", models.IntegerField(blank=True, null=True)),
                ("primary_silph_id", models.IntegerField(blank=True, null=True)),
                (
                    "osm_id",
                    models.IntegerField(blank=True, db_column="OSM_id", null=True),
                ),
            ],
            options={"db_table": "NST_locations", "managed": False},
        ),
        migrations.CreateModel(
            name="NstMetropolisMajor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(db_column="Name", max_length=123)),
                (
                    "shortname",
                    models.CharField(
                        blank=True, db_column="Shortname", max_length=88, null=True
                    ),
                ),
                ("lat", models.FloatField(blank=True, null=True)),
                ("lon", models.FloatField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "admin_names",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
            options={"db_table": "NST_metropolis_major", "managed": False},
        ),
        migrations.CreateModel(
            name="NstNeighborhoods",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=222)),
                ("lat", models.FloatField(blank=True, null=True)),
                ("lon", models.FloatField(blank=True, null=True)),
            ],
            options={"db_table": "NST_neighborhoods", "managed": False},
        ),
        migrations.CreateModel(
            name="NstParkSystem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=123)),
                ("website", models.CharField(blank=True, max_length=234, null=True)),
            ],
            options={"db_table": "NST_park_system", "managed": False},
        ),
        migrations.CreateModel(
            name="NstRotationDates",
            fields=[
                ("num", models.AutoField(primary_key=True, serialize=False)),
                ("date", models.CharField(max_length=11)),
                (
                    "special_note",
                    models.CharField(blank=True, max_length=123, null=True),
                ),
            ],
            options={"db_table": "NST_rotation_dates", "managed": False},
        ),
        migrations.CreateModel(
            name="NstSpeciesListArchive",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "species_txt",
                    models.CharField(blank=True, max_length=111, null=True),
                ),
                ("confirmation", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={"db_table": "NST_species_list_archive", "managed": False},
        ),
        migrations.CreateModel(
            name="Pokemon",
            fields=[
                ("form", models.CharField(max_length=11)),
                (
                    "dex_number",
                    models.IntegerField(
                        db_column="#", primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(db_column="Name", max_length=255)),
                (
                    "total",
                    models.IntegerField(blank=True, db_column="Total", null=True),
                ),
                ("hp", models.IntegerField(db_column="HP")),
                ("attack", models.IntegerField(db_column="Attack")),
                ("defense", models.IntegerField(db_column="Defense")),
                ("spatk", models.IntegerField(db_column="SpAtk")),
                ("spdef", models.IntegerField(db_column="SpDef")),
                ("speed", models.IntegerField(db_column="Speed")),
                (
                    "pogo_nerf",
                    models.IntegerField(blank=True, db_column="PoGoNerf", null=True),
                ),
                ("wt_kg", models.FloatField()),
                ("ht_m", models.FloatField()),
                (
                    "officialcolor",
                    models.CharField(
                        blank=True, db_column="OfficialColor", max_length=11, null=True
                    ),
                ),
                (
                    "description_category",
                    models.CharField(blank=True, max_length=13, null=True),
                ),
                ("nicknames", models.CharField(blank=True, max_length=88, null=True)),
                ("notes", models.CharField(blank=True, max_length=333, null=True)),
                (
                    "nia_cust_hp",
                    models.IntegerField(blank=True, db_column="NIA_cust_HP", null=True),
                ),
                (
                    "nia_cust_atk",
                    models.IntegerField(
                        blank=True, db_column="NIA_cust_ATK", null=True
                    ),
                ),
                (
                    "nia_cust_def",
                    models.IntegerField(
                        blank=True, db_column="NIA_cust_DEF", null=True
                    ),
                ),
            ],
            options={"db_table": "Pokémon", "managed": False},
        ),
        migrations.CreateModel(
            name="TypeEffectiveness",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                )
            ],
            options={"db_table": "type_effectiveness", "managed": False},
        ),
        migrations.CreateModel(
            name="TypeEffectivenessRatings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.CharField(max_length=23)),
                ("dmg_multiplier", models.FloatField()),
                ("pogodamage", models.FloatField(db_column="PoGoDamage")),
                ("oldpogodamage", models.FloatField(db_column="oldPoGoDamage")),
            ],
            options={"db_table": "type_effectiveness_ratings", "managed": False},
        ),
        migrations.CreateModel(
            name="TypeList",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=55, unique=True)),
                ("glitch", models.IntegerField(blank=True, null=True)),
                ("note", models.CharField(blank=True, max_length=111, null=True)),
                ("emoji", models.CharField(blank=True, max_length=8, null=True)),
            ],
            options={"db_table": "type_list", "managed": False},
        ),
        migrations.CreateModel(
            name="ZcCategories",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=22, unique=True)),
                ("note", models.CharField(blank=True, max_length=111, null=True)),
            ],
            options={"db_table": "ZC_categories", "managed": False},
        ),
    ]
