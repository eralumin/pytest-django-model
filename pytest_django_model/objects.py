# coding: utf-8

import inspect

from django.db.models import Field
from django.db.models.fields import related_descriptors
from django.db.models.options import Options

from .utils import get_model_fields, is_dunder

DIRTY_FIELD_ATTRS = ["serialize"]

META_OPTIONS = (
    "abstract",
    "base_manager_name",
    "db_table",
    "db_tablespace",
    "default_manager_name",
    "default_permissions",
    "default_related_name",
    "get_latest_by",
    "index_together",
    "indexes",
    "managed",
    "order_with_respect_to",
    "ordering",
    "permissions",
    "proxy",
    "required_db_features",
    "required_db_vendor",
    "select_on_save",
    "unique_together",
    "verbose_name",
    "verbose_name_plural",
)


RELATED_DESCRIPTORS = tuple(
    [
        getattr(related_descriptors, attr)
        for attr in dir(related_descriptors)
        if not is_dunder(attr) and inspect.isclass(getattr(related_descriptors, attr))
    ]
)


class FieldError(AttributeError, NameError):
    pass


class MetaError(AttributeError, NameError):
    pass


class AttributeObject:
    def __init__(self, name, value, parents, cls=None):
        self.cls = cls if cls else value.__class__
        self.name = name
        self.value = value
        self.parents = self.get_parents(parents)
        self.breadcrumb = f"{self.parents}.{self.name}"

    def get_parents(self, parents):
        if isinstance(parents, (list, tuple)):
            parents_str = ".".join(parents)
        else:
            parents_str = parents

        return parents_str

    def __eq__(self, other):
        if isinstance(other, AttributeObject):
            return self.cls == other.cls and self.value == other.value
        else:
            return self.value == other

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<{self.breadcrumb}: {self.cls.__name__}({self.value})>"


class ModelObject:
    def __init__(self, name, constants, fields, meta):
        # Create Inner Class Meta for Meta Options
        self.Meta = type(f"{name}Meta", (), {})
        # Create Class to store model metadata
        self._meta = type(f"{name}_meta", (), {})

        self._meta.name = name

        self._meta.constants = dict()
        self._meta.fields = dict()
        self._meta.meta = dict()

        # Set Constants
        for constant_name, value in constants.items():
            attr_object = AttributeObject(
                name=constant_name, value=value, parents=self._meta.name
            )
            self._meta.constants[constant_name] = attr_object
            setattr(self, constant_name, attr_object)

        # Set Fields
        for field_name, data in fields.items():
            attr_object = AttributeObject(
                name=field_name,
                cls=data["class"],
                value=data["attrs"],
                parents=self._meta.name,
            )
            self._meta.fields[field_name] = attr_object
            setattr(self, field_name, attr_object)

        # Set Meta
        for option_name, value in meta.items():
            attr_object = AttributeObject(
                name=option_name, value=value, parents=[self._meta.name, "Meta"]
            )
            self._meta.meta[option_name] = attr_object
            setattr(self.Meta, option_name, attr_object)

    def __str__(self):
        return f"{self._meta.name}"

    def __repr__(self):
        join = lambda x: ", ".join(x)
        return (
            f"<{self._meta.name}: constants({join(self._meta.constants)}), "
            f"fields({join(self._meta.fields)}), Meta({join(self._meta.meta)})>"
        )


class ModelGenerator:
    def __call__(self, model, has_id=None):
        """Retrieve Model Fields, Constants and Meta Options and save them as a dict.
        Then create ModelObject and return it.
        """
        self.model = model
        self.constants = self.get_constants()
        self.fields = self.get_fields(has_id)
        self.meta_options = self.get_meta_options()

        model_object = ModelObject(
            name=self.model.__name__,
            constants=self.constants,
            fields=self.fields,
            meta=self.meta_options,
        )

        self.clean_instance()

        return model_object

    @classmethod
    def get_default_meta_options(cls):
        """Generate default options for Meta and return them as a dict.
        """
        default_meta_options = Options(None).__dict__

        cleaned_default_meta_options = dict()
        for attr, value in default_meta_options.items():
            if attr in META_OPTIONS:
                cleaned_default_meta_options[attr] = value

        return cleaned_default_meta_options

    def clean_instance(self):
        """Clean instance for future usage.
        """
        (delattr(self, attr) for attr in tuple(self.__dict__))

    def get_constants(self):
        """Retrieve Constants and return them as a dict.
        """
        attrs = dict(self.model.__dict__)

        constants = dict()
        for attr, value in attrs.items():
            if self.is_constant(attr, value):
                constants[attr] = value

        return constants

    def get_field_attrs(self, field):
        """Retrieve Attributes for given Field and return them as a dict.
        """
        attrs = field.deconstruct()[3]
        field_attrs = dict()
        for attr, value in attrs.items():
            if attr not in DIRTY_FIELD_ATTRS:
                # Replace "to" value by 'self' if the value object is the model itself.
                if (
                    hasattr(self.model, "_meta")
                    and attr == "to"
                    and value == self.model._meta.label
                ):
                    field_attrs[attr] = "self"
                # If the value is callable, replace it by the callable name.
                elif callable(value):
                    field_attrs[attr] = value.__name__
                else:
                    field_attrs[attr] = value

        return field_attrs

    def get_fields(self, has_id):
        """Retrieve Original Fields and return them as a dict.
        """
        # Retrieve list of fields
        fields = get_model_fields(self.model)

        fields_dict = dict()
        for field in fields:
            if has_id is False and field.name == "id":
                continue

            field_attrs = self.get_field_attrs(field)
            fields_dict[field.name] = {"class": field.__class__, "attrs": field_attrs}

        return fields_dict

    def get_meta_options(self):
        """Retrieve Original Meta Options and return them as a dict.
        """
        return {**self.get_default_meta_options(), **self.model._meta.original_attrs}

    def is_constant(self, attr, value):
        """Verify if given attribute is a constant.
        """
        fields = self.model._meta._forward_fields_map.keys()

        if (
            # Ignore Exception Objects.
            type(value) == type
            # Ignore Special Methods.
            or is_dunder(attr)
            # Ignore Django Model Attributes.
            or attr in ("objects", "id", "_meta")
            # Ignore Fields.
            or attr in fields
            # Ignore if is instance of Field.
            or isinstance(value, Field)
            # Ignore Properties.
            or isinstance(value, property)
            # Ignore Descriptors.
            or isinstance(value, RELATED_DESCRIPTORS)
        ):
            return False
        else:
            return True


get_model_object = ModelGenerator()
