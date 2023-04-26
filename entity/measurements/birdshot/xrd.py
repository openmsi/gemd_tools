from typing import ClassVar

from gemd import MeasurementTemplate

from entity.base import Measurement
from entity.base.attributes import AttrsDict, define_attribute, finalize_template

__all__ = ['XRD']

class XRD(Measurement):
    '''Class representing SEM as a measurement '''
    
    TEMPLATE: ClassVar[MeasurementTemplate] = MeasurementTemplate(
        name="XRD",
        description='XRD measurement'
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