from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

# Create your views here.
from .models import NstSpeciesListArchive, NstMetropolisMajor, NstLocation, NstRotationDate


class CityView(generic.ListView):
    model = NstSpeciesListArchive
    template_name = 'nestlist/city.html'
    context_object_name = 'current_nest_list'
    pk_url_kwarg = 'city_id'

    def get_rotation(self):
        return NstRotationDate.objects.filter(date__lte=timezone.now()).order_by('-num')[0]

    def get_queryset(self):
        return NstSpeciesListArchive.objects.filter(nestid__neighborhood__major_city=self.kwargs['city_id'],
                                                    rotation_num=self.get_rotation()).order_by('nestid__official_name')


class IndexView(generic.ListView):
    model = NstMetropolisMajor
    template_name = 'nestlist/index.html'
    context_object_name = 'city_list'

    def get_queryset(self):
        return NstMetropolisMajor.objects.all()


class NestView(generic.DetailView):
    model = NstLocation
    template_name = 'nestlist/nest.html'
