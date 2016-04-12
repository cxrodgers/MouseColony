from django.contrib import admin
from .models import (Mouse, Genotype, Litter, 
    Cage, Person, Task)
# Register your models here.
from django.db.models import Count
import nested_inline.admin

class MouseInline(nested_inline.admin.NestedTabularInline):
    """Nested within Litter, so this is for adding pups"""
    model = Mouse
    extra = 1
    
    # Exclude the stuff that isn't normally specified when adding pups
    exclude = ('manual_dob', 'manual_mother', 'manual_father', 
        'cage', 'sack_date', 'user', 'breeder')
    show_change_link = True    
    
    # How can we make "notes" the right-most field?

class LitterInline(nested_inline.admin.NestedStackedInline):
    """For adding a Litter to a Cage"""
    model = Litter
    extra = 0
    show_change_link = True
    inlines = [MouseInline]

class LitterAdmin(admin.ModelAdmin):
    list_display = ('breeding_cage', 'date_mated', 'age', 
        'date_toeclipped', 'date_weaned',
        'date_checked',  'needs', 'need_date', 'notes',)
    inlines = [MouseInline] 
    list_editable = ('notes', 'date_checked')
    list_filter = ('proprietor',)
    readonly_fields = ('needs', 'need_date')

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
            
    ordering = ('proprietor',)

class CageAdmin(nested_inline.admin.NestedModelAdmin):
    list_display = ('name', 'proprietor', 'litter', 'infos', 
        'needs', 'need_date', 'defunct', 'notes',)
    list_editable = ('notes', 'defunct', )
    
    # This list_filter doesn't seem to be working at all
    list_filter = ('proprietor__name')
    
    ordering = ('defunct', 'proprietor', 'name',)
    readonly_fields = ('infos', 'needs', 'need_date',)
    list_filter = ('proprietor',)
    inlines = [LitterInline]

class MouseAdmin(admin.ModelAdmin):
    #search_fields = ['name']
    
    # This controls the columns that show up on the Admin page for Mouse
    list_display = ('name', 'user', 'dob', 'age', 'sacked', 'sex', 'cage', 
        'breeder', 'genotype', 'litter', 'notes')
    list_editable = ('notes',)
    readonly_fields = ('info', 'age', 'dob', 'mother', 'father', 'sacked',)
    #~ list_display_links = ('name', 'litter', 'cage')
    list_filter = ['genotype__name', 'breeder']
    
    # This controls what you see on the individual mouse page
    # Would be better to break this up into sections
    fieldsets = (
        (None, {
            'fields': ('name', 'dob', 'father', 'mother', 
            'manual_dob', 'manual_father', 'manual_mother',
            'age', 'sack_date', 'sex', 'cage', 'genotype', 'litter', 'notes', 'info'),
            'description': 'Specify manual_dob, manual_father, and manual_mother only if not available in litter info',
        }),
    )
    #ordering = ['dob']

    #~ # Was hoping to get filtering by sacked working, but doesn't seem to
    #~ def get_queryset(self, request):
        #~ qs = super(MouseAdmin, self).get_queryset(request)
        #~ return qs.annotate(is_sacked=Count('sack_date'))
    

class GenotypeAdmin(admin.ModelAdmin):
    ordering = ('name',)

class PersonAdmin(admin.ModelAdmin):
    ordering = ('name',)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('assigned_to', 'created_by', 'notes', 'cage_names',)
    list_editable = ('notes',)

admin.site.register(Mouse, MouseAdmin)
admin.site.register(Genotype, GenotypeAdmin)
admin.site.register(Litter, LitterAdmin)
admin.site.register(Cage, CageAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Task, TaskAdmin)