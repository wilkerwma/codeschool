import io
import yaml
from collections import OrderedDict


class OrderedDumper(yaml.CSafeDumper):
    """
    Handle ordered dictionaries as regular dictionaries on YAML dump.
    """


def dump(data, stream=None, **kwds):
    """Dump YAML data to stream."""

    kwds.setdefault('indent', 2)
    kwds.setdefault('width', 70)
    kwds.setdefault('default_flow_style', False)
    kwds.setdefault('allow_unicode', True)

    def to_dict(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items()
        )

    OrderedDumper.add_representer(OrderedDict, to_dict)
    return yaml.dump(data, stream, OrderedDumper, **kwds)


def dumps(data, **kwargs):
    """
    Return a string of YAML data.
    """

    return dump(data, None, **kwargs)


def load(stream, **kwargs):
    """
    Load a stream of YAML data.
    """
