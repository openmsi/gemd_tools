from typing import ClassVar

from gemd import MeasurementTemplate

from entity.base import Measurement
from entity.base.attributes import AttrsDict, define_attribute, finalize_template

__all__ = ['Weighting']

class Weighting(Measurement):
    '''Class representing weighting as a measurement '''
    
    TEMPLATE: ClassVar[MeasurementTemplate] = MeasurementTemplate(
        name="Weighting",
        description='The measurement of weight'
    )

    _ATTRS: ClassVar[AttrsDict] = {'conditions': {}, 'parameters': {}, 'properties': {}}

    # define_attribute(
    #     _ATTRS,
    #     template=ParameterTemplate(
    #         name='Supplier',
    #         bounds=CategoricalBounds(categories=[''])
    #     ),
    #     default_value=NominalCategorical('')
    # )

    finalize_template(_ATTRS, TEMPLATE)