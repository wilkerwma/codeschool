from django.db import models

#
# migrate to fields
#

class Measurement(models.Model):
    alias = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=200)
    standard_unit = models.ForeignKey('MeasurementUnit')

    @classmethod
    def autofill(cls):
        data = dict(
            nondimensional=dict(
                name = 'Non-dimensional unity',
                unit = ('', 'None'),
            ),
            length=dict(
                unit = ('m', 'Meter  (SI)'),
            ),
            time=dict(
                unit = ('s', 'Second  (SI)'),
            ),
            mass=dict(
                unit = ('kg', 'Kilogram (SI)'),
            ),
            current=dict(
                unit = ('A', 'Ampere (SI)'),
            ),
            temperature=dict(
                unit = ('K', 'Kevin (SI)'),
            ),
            ammount=dict(
                name = 'Ammount of substance',
                unit = ('mol', 'Mole (SI)'),
            ),
            light=dict(
                name = 'Luminous intensity',
                unit = ('cd', 'Candela (SI)'),
            ),
        )


class MeasurementUnit(models.Model):
    alias = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=200)
    group = models.CharField(max_length=200)
    numer = models.IntegerField(default=1)
    denom = models.IntegerField(default=1)
    power = models.IntegerField(default=0)
    shift = models.FloatField(default=0)
    si_prefixes = dict(
            yotta=('Y', 24),
            zetta=('Z', 21),
            exa=('E', 18),
            peta=('P', 15),
            tera=('T', 12),
            giga=('G', 9),
            mega=('M', 6),
            kilo=('k', 3),
            hecto=('h', 2),
            deka=('da', 1),
            deci=('d', -1),
            centi=('c', -2),
            milli=('m', -3),
            micro=('u', -6),
            nano=('n', -9),
            pico=('p', -12),
            femto=('f', -15),
            atto=('a', -18),
            zepto=('z', -21),
            yocto=('y', -24),
        )


    @classmethod
    def autofill(cls):
        if not Measure.is_autofilled:
            Measure.autofill()

        for unit in 'm s A K cd mol'.split():
            pass

        # SI uses kg as default mass unit. We have to deal with it separately
