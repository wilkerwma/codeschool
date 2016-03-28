class BaseUnitField:
    pass


class UnitField(BaseUnitField):
    pass


class LengthField(BaseUnitField):
    base_unit = 'meter'


class DurationField(BaseUnitField):
    base_unit = 'second'


class MassField(BaseUnitField):
    base_unit = 'kilogram'


class AngleField(BaseUnitField):
    base_unit = 'radian'


class ElectricCurrentField(BaseUnitField):
    base_unit = 'ampere'