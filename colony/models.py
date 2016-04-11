"""
TODO
Validation scripts that check that the genotype of each mouse meshes with
the parents
Auto-determine needed action for each litter (and breeding cage?)
Auto-id litters
Slug the mouse name from the litter name and toe num?
"""


from __future__ import unicode_literals

from django.db import models
import datetime

# Create your models here.

class Person(models.Model):
    name = models.CharField(max_length=15, unique=True)    
    
    def __str__(self):
        return self.name

class Task(models.Model):
    assigned_to = models.ForeignKey('Person', related_name='assigned_to')
    created_by = models.ForeignKey('Person', related_name='created_by')
    notes = models.CharField(max_length=150)
    cages = models.ManyToManyField('Cage', blank=True)
    
    def cage_names(self):
        cage_l=[]
        for c in self.cages.all():
            cage_l.append(c.name)
        return ', '.join(cage_l)
    
class Cage(models.Model):
    name = models.CharField(max_length=10, unique=True)    
    notes = models.CharField(max_length=100, blank=True, null=True)
    defunct = models.BooleanField(default=False)
    location = models.IntegerField(
        choices = (
            (0, '1710'),
            (1, '1702'),
            (2, 'Behavior'),
            ),
        default=0
        )
    
    # Needs to be made mandatory
    proprietor = models.ForeignKey('Person')

    def n_mice(self):
        return len(self.mouse_set.all())
    
    def names(self):
        name_l = []
        for m in self.mouse_set.all():
            name_l.append(m.name)
        return ', '.join(name_l)
    
    def infos(self):
        info_l = [m.info() for m in self.mouse_set.all()]
        return '<pre>' + '<br>'.join(info_l) + '</pre>'
    
    infos.allow_tags = True
    infos.short_description = "Mouse Info"

    def age(self):
        age = None
        for mouse in self.mouse_set.all():
            if age is None:
                age = mouse.age()
            elif age != mouse.age():
                return None
        return age
    
    def __str__(self):
        return self.name

class Genotype(models.Model):
    name = models.CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name

class Mouse(models.Model):
    name = models.CharField(max_length=15, unique=True)
    manual_dob = models.DateField('date of birth', blank=True, null=True)
    litter = models.ForeignKey('Litter', null=True, blank=True)
    sack_date = models.DateField('sac date', blank=True, null=True)
    notes = models.CharField(max_length=100, null=True, blank=True)    
    sex = models.IntegerField(
        choices=(
            (0, 'M'),
            (1, 'F'),
            (2, '?'),
            )
        )
    
    # Link it to a cage
    cage = models.ForeignKey(Cage, null=True, blank=True)
    genotype = models.ForeignKey(Genotype)
    
    @property
    def dob(self):
        """Auto dob
        
        Idea is that most of the time the dob doesn't have to specified bc
        we get it from the litter. So remove it from the inline.
        
        However in some cases we don't have litter, so allow user to specify
        manually in those cases.
        
        Then this is a read-only field to present the correct dob.
        """
        if self.manual_dob is not None:
            return self.manual_dob
        elif self.litter is not None:
            return self.litter.dob
        else:
            return None
    
    def info(self):
        """Returns TRAINING_NAME || NAME (SEX, AGE, GENOTYPE)
        
        """
        age = self.age()
        if age is None:
            return "%s (%s %s)" % (
                str(self.name),
                str(self.genotype),
                str(self.get_sex_display()),
                )
        else:
            return "%s (P%d %s %s)" % (
                str(self.name),
                self.age(),
                str(self.genotype),
                str(self.get_sex_display()),
                )
    
    def age(self):
        if self.dob is None:
            return None
        today = datetime.date.today()
        return (today - self.dob).days
    
    def __str__(self):
        return str(self.name)
        
    def save(self, *args, **kwargs):
        # Looks like this makes sure that new mice are saved with the
        # litter's DOB?
        if self.litter and not self.pk:
            self.manual_dob = self.litter.dob
        return super(Mouse, self).save(*args, **kwargs)

class Litter(models.Model):
    date_mated = models.DateField('parents mated', null=True, blank=True)
    dob = models.DateField('date of birth', null=True, blank=True)
    date_toeclipped = models.DateField('toe clip', null=True, blank=True)
    date_weaned = models.DateField('weaned', null=True, blank=True)
    date_checked = models.DateField('last checked', null=True, blank=True)
    
    proprietor = models.ForeignKey(Person, default=1)
    
    notes = models.CharField(max_length=100, null=True, blank=True)
    pcr_info = models.CharField(max_length=50, null=True, blank=True)
    needs = models.CharField(max_length=50, null=True, blank=True)
    need_date = models.DateField('needs on', null=True, blank=True)


    father = models.ForeignKey('Mouse',
        null=True, blank=True, related_name='bc_father',
        limit_choices_to={'sex': 0})
    mother = models.ForeignKey('Mouse',
        null=True, blank=True, related_name='bc_mother',
        limit_choices_to={'sex': 1})
    
    # A one-to-one key to Cage, because each Cage can have no more than
    # one litter
    # Not sure whether to set primary_key=True here
    # If we set it true, it implie null=False and unique=True
    # Probably this is good because it will auto-create a Litter for every
    # new Cage, which may save a manual step?
    breeding_cage = models.OneToOneField(Cage,
        on_delete=models.CASCADE,
        primary_key=True)
    
    def age(self):
        if self.dob is None:
            return None
        today = datetime.date.today()
        return (today - self.dob).days

    def __str__(self):
        return str(self.breeding_cage.name)
    
    @property
    def name(self):
        return self.breeding_cage.name
    
    def _needs(self):
        """View column in admin that triggers update_needs
        
        When the admin requests this, it calls update_needs, which sets
        needs and need_date. This returns needs.
        
        Seems like there is a slight race condition in that need_date might
        be requested before needs, which means it would be stale. But
        refreshing would fix this..
        """
        self.update_needs()
        return self.needs
        
    def update_needs(self):
        """Automatically determine next needed action and date.
        
        Sets the fields "needs" and "need_date".
        """
        if self.date_weaned is not None:
            # Already weaned
            self.needs = None
            self.need_date = None
        elif self.date_toeclipped is not None:
            # Already toe clipped, needs wean
            if self.dob is None:
                self.needs = "provide dob"
                self.need_date = datetime.date.today()
                return
            self.need_date = self.dob + datetime.timedelta(days=19)
            self.needs = "wean on P19"
        elif self.dob is not None:
            # Born, but not toe clipped
            self.need_date = self.dob + datetime.timedelta(days=7)
            self.needs = "toe clip on P7"
        elif self.date_mated is not None:
            # Not born yet
            self.need_date = self.date_mated + datetime.timedelta(days=25)
            
            # If it was checked since the target date, extend by 4 days
            if self.date_checked is not None and self.date_checked > self.need_date:
                self.need_date = self.date_checked + datetime.timedelta(days=4)
            
            # Recalculate the time taken
            gestation_period = (self.need_date - self.date_mated).days
            self.needs = "check for pups on day %d" % gestation_period
        else:
            # Not even mated
            self.needs = "parent"
            self.need_date = datetime.date.today()
            
    def save(self, *args, **kwargs):
        if self.breeding_cage and not self.pk:
            self.proprietor = self.breeding_cage.proprietor
        return super(Litter, self).save(*args, **kwargs)

    