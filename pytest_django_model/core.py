# coding: utf-8

from inspect import isclass, isfunction

from django.db.models import Field, Model
from django.db.models.base import ModelBase

from .file import FileGenerator
from .objects import get_model_object
from .utils import a_or_an, delete_django_model, is_dunder, pytest_exit


class InvalidModelError(AttributeError, NameError):
    pass


class ModelNotFoundError(AttributeError, NameError):
    pass


def get_invalid_model_msg(obj):
    if not isclass(obj):
        obj_type = obj.__class__.__name__
        msg = f"'{obj}' is {a_or_an(obj_type)} {obj_type}, not a class."
    else:
        msg = f"'{obj.__name__}' isn't a valid Django Model."

    return msg


def is_django_model_attr(attr, value):
    """Check if the given attribute is a Django Model attr or a Test Class attr.
    """
    if is_dunder(attr) or isfunction(value) or isinstance(value, property):
        return False
    else:
        return True


class PytestDjangoModel(type):
    def __new__(cls, name, bases, dct):
        # Retrieve Data
        ###############
        meta = cls.get_meta(cls, name, dct)

        original = cls.get_original(cls, meta)
        original_name = original._meta.object_name

        parents = cls.get_parents(cls, meta)

        tester_name = name
        tester_has_id = isinstance(dct.get("id", None), Field)
        tester = cls.get_tester(cls, tester_name, dct, original, parents)

        # Validate Data
        ###############
        cls.validate_data(cls, name, tester, tester_name, original_name)

        # Create Data
        #############
        OriginalObject = get_model_object(original)
        TesterObject = get_model_object(tester, has_id=tester_has_id)
        # Remove tester from django cache
        delete_django_model(original._meta.app_label, tester_name)

        # Get Test Functions
        generated_file = FileGenerator(OriginalObject, TesterObject)
        test_functions = generated_file.get_functions()

        # Create Class
        ##############
        # Create Clean new_dct.
        new_dct = cls.get_cleaned_dct(cls, dct)

        # Reinjecting TesterObject dict to new_dct.
        tester_dct = dict(TesterObject.__dict__)
        new_dct.update(cls.inject_tester_dct(cls, dct, tester_dct))

        # Add OriginalObject to dct.
        new_dct["_meta"].model = OriginalObject

        # Inject test_functions to new_dct.
        new_dct.update(test_functions)

        return super().__new__(cls, name, bases, new_dct)

    def get_meta(cls, cls_name, dct):
        """Retrieve Meta, raise an Error if it isn't found.
        """
        try:
            return dct["Meta"]
        except KeyError:
            error_msg = (
                f"{cls_name} must have a 'Meta' inner class with 'model' attribute."
            )
            raise ModelNotFoundError(error_msg)

    def get_original(cls, meta):
        """Retrieve Original Model, raise an Error if it isn't found.
        """
        try:
            if hasattr(meta, "model"):
                model = meta.model
                delattr(meta, "model")
            else:
                model = NotImplemented

            if model is NotImplemented:
                message = f"'Meta' inner class has not 'model' attribute."
                raise ModelNotFoundError(message)
            elif not isinstance(model, ModelBase):
                error_msg = get_invalid_model_msg(model)
                raise InvalidModelError(error_msg)
            else:
                return model
        except Exception as e:
            pytest_exit(e)

    def get_parents(cls, meta):
        """Retrieve Parents Models and return them as dict.
        """
        if hasattr(meta, "parents"):
            try:
                parents = meta.parents
                delattr(meta, "parents")
                # Checks that the object itself is a Django Model.
                if isinstance(parents, ModelBase):
                    return (parents,)
                # Else iterates on the object if it's a list or a tuple..
                elif isinstance(parents, (list, tuple)):
                    for parent in parents:
                        # Raise an Error if any element isn't a Django Model.
                        if not isinstance(parent, ModelBase):
                            error_msg = get_invalid_model_msg(parent)
                            raise InvalidModelError(
                                f"'parents' contains invalid model: {error_msg}"
                            )
                    else:
                        return tuple(parents)
                # Else raise an Error because object it isn't a Django Model.
                else:
                    error_msg = get_invalid_model_msg(parents)
                    raise InvalidModelError(f"'parents': {error_msg}")
            except Exception as e:
                pytest_exit(e)
        else:
            return None

    def get_cleaned_tester(cls, dct):
        """Return a cleaned copy of dct for TesterObject.
        """
        return {
            attr: value
            for attr, value in dct.items()
            if is_django_model_attr(attr, value)
        }

    def get_tester(cls, name, dct, original, parents):
        """Make a cleaned copy of the given class and return it.
        """
        dct = cls.get_cleaned_tester(cls, dct)

        # Add Original Module
        dct["__module__"] = original.__module__
        # Create Django Model
        if not parents:
            parents = (Model,)

        return type(name, parents, dct)

    def validate_data(cls, name, tester, tester_name, original_name):
        levels = {
            50: "Critical",
            40: "Error",
            30: "Warning",
            20: "Info",
            10: "Debug",
            0: "Notset",
        }

        try:
            errors = tester.check()
            if errors:
                msg = f"The {name} Model get the following errors during validation:\n"
                for error in errors:
                    error_msg = error.msg.replace(tester_name, original_name)

                    if isinstance(error.obj, Field):
                        error_type = error.obj.name
                    else:
                        error_type = "Meta"

                    msg += f"  - {error_type}: {levels[error.level]}: {error_msg}\n"

                raise InvalidModelError(msg)
        except Exception as e:
            pytest_exit(e)

    def get_cleaned_dct(cls, dct):
        """Return a cleaned copy of dct for Test Class.
        """
        return {
            attr: value
            for attr, value in dct.items()
            if not is_django_model_attr(attr, value)
        }

    def inject_tester_dct(cls, dct, tester_dct):
        meta, tester_meta = dct["Meta"], tester_dct.get("Meta", None)

        for option, value in tester_meta.__dict__.items():
            if not is_dunder(option):
                setattr(meta, option, value)

        for attr, value in tester_dct.items():
            if is_django_model_attr(attr, value):
                dct[attr] = value

        return dct

    def __repr__(cls):
        join = lambda x: ", ".join(x)
        return (
            f"<{cls.__name__}: constants({join(cls._meta.constants)}), "
            f"fields({join(cls._meta.fields)}), Meta({join(cls._meta.meta)})>"
        )
