"""
Could also be called the Amorphous Cup

Outputs to a .log file to play nice with .gitignore
"""
from typing import Set
import sys
import os

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pokedb.settings")

# Setup django
import django

django.setup()
from speciesinfo.models import enabled_in_pogo, match_species_by_type, Pokemon
from nestlist.utils import decorate_text

egg = Pokemon.objects.get(name="(Egg)")
everyone = enabled_in_pogo()
big_boys = set(Pokemon.objects.filter(evolves_to=None))
pure_psychic = set(
    match_species_by_type("Psychic", input_list=everyone, second_type="mono")
)
ghosts = set(match_species_by_type("Ghost", input_list=everyone, second_type="mono"))

shapeshift: "Set[Pokemon]" = set()
checked: "Set[Pokemon]" = set()
errors: "Set[Pokemon]" = set()
ineligible: "Set[Pokemon]" = pure_psychic

for sp in set(big_boys):
    # print(sp)
    if sp in checked:
        # print(f"xx {sp}")
        continue
    checked.add(sp)
    try:
        fft = set(sp.full_family_tree())
        fl = sp.prior_stages()
    except AttributeError:
        # print(f"AE! {sp} AE!")
        errors.add(sp)
        continue
    if fft != set(fl) or "mega" in sp.form.lower():
        shapeshift |= fft
        # print(f"{sp}..yes")
    else:
        # print(f"no {sp}")
        ineligible.add(sp)
        pass
    checked |= fft

path = "shapeshifter.log"
species_file = open(path, "w")


def headers(txt: str) -> str:
    return decorate_text(txt, "==[  ]==") + "\n"


species_file.write(headers("Shapeshifter Core"))
for sp in sorted((shapeshift & set(everyone)) - pure_psychic):
    species_file.write(str(sp) + "\n")

species_file.write(headers("Errors"))
for err in sorted(errors):
    species_file.write(str(err) + "\n")

species_file.write(headers("Banned Psychics"))
for p in sorted(pure_psychic & shapeshift):
    species_file.write(str(p) + "\n")

species_file.write(headers("Spooky Ghosts"))
for g in sorted(ghosts - shapeshift):
    species_file.write(str(g) + "\n")

species_file.write(headers("N/A"))
for g in sorted(ineligible - pure_psychic):
    species_file.write(str(g) + "\n")

species_file.close()
