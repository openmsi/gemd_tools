'''Attribute functions and templates used elsewhere.'''

from typing import TypedDict, Type, Union, Optional, Any, get_args

from gemd import (
    ConditionTemplate, ParameterTemplate, PropertyTemplate,
    Condition, Parameter, Property, PropertyAndConditions
)
from gemd.entity.template.attribute_template import AttributeTemplate
from gemd.entity.attribute.base_attribute import BaseAttribute
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.value.base_value import BaseValue
from gemd.enumeration import Origin

from .typing import Temp, Spec, Run, SpecOrRun, SpecRunLiteral

class AttrDict(TypedDict):
    '''
    Define dictionary for specifying required/optional attribute templates with defaults.

    If ``bounds`` is not ``None``, it will be added as a more restrictive set
    of bounds to the attribute in the template.

    If ``default_value`` is ``None``, the attribute is optional. Otherwise, it
    is required and should be added to the spec upon instantiation with the
    default value (in subclasses).
    '''

    bounds: Optional[BaseBounds]
    default_value: Optional[BaseValue]

class CondDict(AttrDict):
    '''Add condition template key.'''

    cond: ConditionTemplate

class ParamDict(AttrDict):
    '''Add parameter template key.'''

    param: ParameterTemplate

class PropDict(AttrDict):
    '''Add property template key.'''

    prop: PropertyTemplate

class AttrsDict(TypedDict, total=False):
    '''Define dictionary containing local attributes.'''

    conditions: dict[str, CondDict]
    parameters: dict[str, ParamDict]
    properties: dict[str, PropDict]

def define_attribute(
    cls_attrs: AttrsDict,
    template: AttributeTemplate,
    bounds: Optional[BaseBounds] = None,
    default_value: Optional[BaseValue] = None
    ) -> None:
    '''
    Add attribute `template` to `cls_attrs`.

    Use as needed at the beginning of each subclass.
    '''

    if isinstance(template, ConditionTemplate):
        key1 = 'conditions'
        key2 = 'cond'
    elif isinstance(template, ParameterTemplate):
        key1 = 'parameters'
        key2 = 'param'
    elif isinstance(template, PropertyTemplate):
        key1 = 'properties'
        key2 = 'prop'
    else:
        raise TypeError(
            'template must be an instance of ConditionTemplate, '
            'ParameterTemplate, or PropertyTemplate.'
        )

    if bounds is not None and not isinstance(bounds, BaseBounds):
        raise TypeError('bounds must be an instance of BaseBounds.')

    if default_value is not None and not isinstance(default_value, BaseValue):
        raise TypeError('default_value must be an instance of BaseValue.')

    cls_attrs[key1][template.name] = {
        key2: template,
        'bounds': bounds,
        'default_value': default_value
    }

def finalize_template(cls_attrs: AttrsDict, cls_template: Temp) -> None:
    '''
    Add conditions, parameters, and properties to ``cls_template``.

    Use in subclasses after all ``define_attribute`` calls.
    '''

    if cls_attrs.get('conditions') is not None:
        cls_template.conditions = [
            (cond_dict['cond'], cond_dict['bounds'])
            for cond_dict in cls_attrs['conditions'].values()
        ]

    if cls_attrs.get('parameters') is not None:
        cls_template.parameters = [
            (param_dict['param'], param_dict['bounds'])
            for param_dict in cls_attrs['parameters'].values()
        ]

    if cls_attrs.get('properties') is not None:
        cls_template.properties = [
            (prop_dict['prop'], prop_dict['bounds'])
            for prop_dict in cls_attrs['properties'].values()
        ]

def update_attrs(
    attrs: AttrsDict,
    spec: Spec,
    run: Run,
    AttrType: Type[Union[BaseAttribute, PropertyAndConditions]],
    attributes: tuple[BaseAttribute],
    replace_all: bool = False,
    which: SpecRunLiteral = 'spec'
    ) -> None:
    '''Used by BaseNode to update attributes and link attribute templates.'''

    attr_dict_key, singular, plural = _validate_attr_type(AttrType)
    validate_which(which)

    required_attrs = _required_attrs(attrs, AttrType, attr_dict_key, plural)
    
    for attr in attributes:
        if attr.name not in attrs[plural]:
            raise ValueError(f'{singular.capitalize()} "{attr.name}" is not supported.')

    supplied_attrs = {attr.name: attr for attr in attributes}

    for attr_name, attr in supplied_attrs.items():
        # print(attr_name)
        # print(attr)
        # print("-")
        # print(plural)
        # print(attr_name)
        # print(attr_dict_key)
        if type(attr) == PropertyAndConditions:
            attr.property.template = attrs[plural][attr_name][attr_dict_key]
        else:
            attr.template = attrs[plural][attr_name][attr_dict_key]

    if which in ['spec', 'both']:
        _set_attrs(spec, required_attrs, supplied_attrs, AttrType, replace_all)
    if which in ['run', 'both']:
        _set_attrs(run, required_attrs, supplied_attrs, AttrType, replace_all)

def _required_attrs(
    attrs: AttrsDict,
    AttrType: Type[Union[BaseAttribute, PropertyAndConditions]],
    attr_dict_key: str,
    plural: str
    ) -> Union[BaseAttribute, PropertyAndConditions]:
    '''
    Return dict of required attributes, handling case of ``PropertyAndConditions`` for materials.
    '''

    if AttrType is PropertyAndConditions:
        return {
            attr_name: PropertyAndConditions(
                property=Property(
                    name=attr_name,
                    value=attr_dict['default_value'],
                    template=attr_dict[attr_dict_key],
                    origin=Origin.SPECIFIED
                )
            )
            for attr_name, attr_dict in attrs[plural].items()
            if attr_dict['default_value'] is not None
        }

    return {
        attr_name: AttrType(
            name=attr_name,
            value=attr_dict['default_value'],
            template=attr_dict[attr_dict_key],
            origin=Origin.SPECIFIED
        )
        for attr_name, attr_dict in attrs[plural].items()
        if attr_dict['default_value'] is not None
    }

def _set_attrs(
    spec_or_run: SpecOrRun,
    required_attrs: dict[str, BaseAttribute],
    supplied_attrs: dict[str, BaseAttribute],
    AttrType: Type[Union[BaseAttribute, PropertyAndConditions]],
    replace_all: bool
    ) -> None:
    '''Set spec or run attributes appropriately, depending on `AttrType`.'''

    if AttrType is Condition:
        existing_attrs = {} if replace_all else {attr.name: attr for attr in spec_or_run.conditions}
        spec_or_run.conditions = {**required_attrs, **existing_attrs, **supplied_attrs}.values()
    elif AttrType is Parameter:
        existing_attrs = {} if replace_all else {attr.name: attr for attr in spec_or_run.parameters}
        spec_or_run.parameters = {**required_attrs, **existing_attrs, **supplied_attrs}.values()
    elif AttrType in [Property, PropertyAndConditions]:
        existing_attrs = {} if replace_all else {attr.name: attr for attr in spec_or_run.properties}
        spec_or_run.properties = {**required_attrs, **existing_attrs, **supplied_attrs}.values()

def remove_attrs(
    attrs: AttrsDict,
    spec: Spec,
    run: Run,
    AttrType: Type[Union[BaseAttribute, PropertyAndConditions]],
    attr_names: tuple[str, ...],
    which: SpecRunLiteral = 'spec'
    ) -> None:
    '''Used by BaseNode to remove attributes by name.'''

    _, singular, plural = _validate_attr_type(AttrType)
    validate_which(which)

    required_names = [
        attr_name for attr_name, attr_dict, in attrs[plural].items()
        if attr_dict['default_value'] is not None
    ]

    for name in attr_names:
        if name not in attrs[plural]:
            raise ValueError(f'{singular.capitalize()} "{name}" is not supported.')
        if name in required_names:
            raise ValueError(f'May not remove required {singular} "{name}".')

    if which in ['spec', 'both']:
        _remove_attrs(AttrType, spec, attr_names)
    if which in ['run', 'both']:
        _remove_attrs(AttrType, run, attr_names)

def _remove_attrs(
    AttrType: Type[Union[BaseAttribute, PropertyAndConditions]],
    spec_or_run: SpecOrRun,
    attr_names: tuple[str, ...]
    ) -> None:
    '''Remove spec or run attributes appropriately, depending on `AttrType`.'''

    if AttrType is Condition:
        left_over = [attr for attr in spec_or_run.conditions if attr.name not in attr_names]
        spec_or_run.conditions = left_over
    elif AttrType is Parameter:
        left_over = [attr for attr in spec_or_run.parameters if attr.name not in attr_names]
        spec_or_run.parameters = left_over
    elif AttrType in [Property, PropertyAndConditions]:
        left_over = [attr for attr in spec_or_run.properties if attr.name not in attr_names]
        spec_or_run.properties = left_over

def _validate_attr_type(AttrType: Any) -> None:
    '''Check `AttrType`, return case-specific strings.'''

    if AttrType is Condition:
        attr_dict_key = 'cond'
        singular = 'condition'
        plural = 'conditions'
    elif AttrType is Parameter:
        attr_dict_key = 'param'
        singular = 'parameter'
        plural = 'parameters'
    elif AttrType in [Property, PropertyAndConditions]:
        attr_dict_key = 'prop'
        singular = 'property'
        plural = 'properties'
    else:
        raise ValueError(
            'AttrType must be one of Condition, Parameter, Property, or PropertyAndConditions.'
        )

    return attr_dict_key, singular, plural

def validate_which(which: Any) -> None:
    '''Validate `which`.'''

    if which not in get_args(SpecRunLiteral):
        raise ValueError(f'which must be one of {get_args(SpecRunLiteral)}')
