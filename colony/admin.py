from django.contrib import admin
from .models import (Mouse, Genotype, Litter, 
    BreedingCage, Cage, Person)
# Register your models here.
from django.db.models import Count


class MouseInline(admin.TabularInline):
    model = Mouse
    extra = 1
    show_change_link = True    

class LitterInline(admin.TabularInline):
    model = Litter
    extra = 1
    show_change_link = True

class LitterAdmin(admin.ModelAdmin):
    list_display = ('name', 'breeding_cage', 'date_mated', 'dob', 
        'date_toeclipped', 'date_weaned',
        'date_checked', 'notes', '_needs', 'need_date')
    inlines = [MouseInline] 
    list_editable = ('notes', 'date_weaned', 'date_checked')
    readonly_fields = ('_needs', 'need_date')

    def get_queryset(self, request):
        """Override the ordering to put future litters at the top"""
        qs = super(LitterAdmin, self).get_queryset(request)
        
        # Put the ones with no DOB first
        # Then the ones with no date of weaning
        # And for everyone else, sort in reverse chronological
        return qs.\
            annotate(dob_is_null=Count('dob')).\
            annotate(dwe_is_null=Count('date_weaned')).\
            order_by('dob_is_null', 'dwe_is_null', '-dob')

class CageAdmin(admin.ModelAdmin):
    list_display = ('name', 'infos', 'defunct', 'notes',)
    list_editable = ('notes',)
    ordering = ('defunct', 'name')
    readonly_fields = ('infos',)
    inlines = [MouseInline]

class BreedingCageAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'infos', 'defunct',
        'target_genotype', 'notes', 'father', 'mother', 'litter_needs')
    list_editable = ('defunct', 'notes')
    #~ list_display_links = ('father', 'mother',)
    readonly_fields = ('n_mice', 'names', 'target_genotype', 'infos', 'litter_needs')
    ordering = ('defunct', 'name',)
    inlines = [MouseInline, LitterInline]

class MouseAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'age', 'sack_date', 'sex', 'dob', 'cage', 
        'genotype', 'litter', 'notes')
    list_editable = ('sack_date', )
    readonly_fields = ('info', 'age',)
    #~ list_display_links = ('name', 'litter', 'cage')
    list_filter = ['genotype', 'sack_date']
    ordering = ['dob']

class GenotypeAdmin(admin.ModelAdmin):
    ordering = ('name',)

class PersonAdmin(admin.ModelAdmin):
    ordering = ('name',)

admin.site.register(Mouse, MouseAdmin)
admin.site.register(BreedingCage, BreedingCageAdmin)
admin.site.register(Genotype, GenotypeAdmin)
admin.site.register(Litter, LitterAdmin)
admin.site.register(Cage, CageAdmin)
admin.site.register(Person, PersonAdmin)