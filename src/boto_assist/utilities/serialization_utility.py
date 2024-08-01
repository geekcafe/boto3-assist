"""Serialization Utility"""

import jsons
from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()


class Serialization:
    """
    Serliaztion Class
    """

    @staticmethod
    def convert_object_to_dict(model) -> object:
        """
        Dumps an object to dictionary structure
        """
        dump = jsons.dump(model, strip_privates=True)
        return dump

    @staticmethod
    @tracer.capture_method
    def map(source: object, target: object) -> object | None:
        """Map an object from one object to another"""
        source_dict: dict = None
        if isinstance(source, dict):
            source_dict = source
        else:
            source_dict = Serialization.convert_object_to_dict(source)

        return Serialization.load_properties(source_dict, target=target)

    @staticmethod
    @tracer.capture_method
    def load_properties(source: dict, target: object) -> object | None:
        """
        converts a source to an object
        """

        # we need a loaded object
        if not isinstance(target, object):
            target = target()

        if isinstance(target, type):
            # create a new instance
            target = target()

        if hasattr(source, "__dict__"):
            source = source.__dict__

        try:
            for attr in dir(target):
                # Skip private and special methods
                if not attr.startswith("_"):
                    value = source.get(attr)

                    if isinstance(value, dict):
                        obj = getattr(target, attr)
                        if obj:
                            attr = Serialization.load_properties(value, obj)
                    if value is not None:
                        if isinstance(attr, str):
                            try:
                                setattr(target, attr, value)
                            except:  # noqa: E722, pylint: disable=bare-except
                                # this will occur on things like methods
                                pass

            return target
        except Exception as e:  # pylint: disable=w0718
            logger.exception(str(e))
            return None
