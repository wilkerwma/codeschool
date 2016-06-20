import json
from collections import OrderedDict
from datetime import date, datetime


class SerializationMixin:
    # Simplified serialization and deserialization
    _serialization_exclude_fields = {'id'}

    @classmethod
    def load(cls, data, format='yaml', **kwargs):
        """
        Load object from data in the given format.

        Data can be a file descriptor or a string.
        """

        try:
            # We don't want to call the load_bulk method of pages
            if format == 'bulk':
                raise ValueError
            loader = getattr(data, 'load_' + format)
        except (AttributeError, ValueError):
            raise ValueError('invalid format: %r' % format)
        else:
            return loader(data, **kwargs)

    @classmethod
    def load_yaml(cls, data, **kwargs):
        """
        Load object from a YAML representation.
        """
        from codeschool import yaml

        py_data = yaml.load(data)
        return cls.load_python(py_data)

    @classmethod
    def load_json(cls, data, **kwargs):
        """
        Load object from a JSON representation.
        """
        if isinstance(data, str):
            py_data = json.loads(data)
        else:
            py_data = json.load(data)
        return cls.load_python(data, **kwargs)

    @classmethod
    def load_python(cls, data, **kwargs):
        """
        Load object from a Python composition of dicts and lists.
        """

        memo = kwargs.get('memo', {})
        if isinstance(data, dict):
            return cls._load_python(data, memo)

        # We create a memo dictionary mapping all data elements with their
        # respective keys. The elements in this dictionary will be gradually
        # replaced by the deserialized versions
        for item in data:
            key = (item['type/model'], item['id'])
            memo[key] = item

        for item in data:
            raise NotImplemented

    @classmethod
    def _load_python_single(cls, data, memo):
        """
        Python loader for single objects.
        """

    def _get_serialization_fields_blacklist(self):
        """
        Return a list of fields that should be excluded from automatic
        serialization.

        You may exclude a field to handle it manually in the serialize method.
        """

        return self._serialization_exclude_fields

    def _get_serialization_extra_fields(self):
        """
        Return a list of additional attributes that will be inserted in the
        serialized object.
        """

        return []

    def _get_serialization_extra(self):
        """
        Returns either a mapping of extra keys to be inserted on the resulting
        serialized object or a tuple of (mapping, idx) where idx is the index
        in which the new values will be inserted.
        """

        fields = self._get_serialization_extra_fields()
        return OrderedDict([(f, getattr(self, f, None)) for f in fields])

    def _get_serialization_id(self):
        """
        Return a string/int/tuple that represents the objects id.
        """

        return self.url_path[1:].partition('/')[-1].strip('/')

    def dump(self, format='yaml', **kwargs):
        """
        Serialize object to the given format.

        The default format chosen in Codeshool is YAML. However different
        subclasses may pick up different default persistence formats.
        """

        try:
            serializer = getattr(self, 'serialize_' + format)
        except AttributeError:
            fmt = self.__class__.__name__, format
            raise ValueError(
                '%s objects do not support serialization to %r' % fmt
            )
        else:
            return serializer(**kwargs)

    def dump_python(self, together=None, parents=0, siblings=0, **kwargs):
        """
        Serialize object to a structure of Python dictionaries and lists.
        """

        # Check if serialization will be of a single or multiple elements
        if parents or siblings:
            if parents == -1:
                parents = self.depth - 1
            if siblings == -1:
                siblings = self.depth - 1

            # We now add all children and parent to the list
            together = list(together or ())[::-1]
            roots = reversed(self.get_ancestors())
            for idx, parent in enumerate(roots):
                if idx < parents:
                    together.append(parent)
                if idx < siblings:
                    together.extend(parent.get_children())
            together.reverse()

        # We check if we need the multi-object or single object serializer.
        if together is not None:
            if self not in together:
                together.append(self)
            out = []
            for item in together:
                item = item.specific
                try:
                    serializer = item._dump_python

                # We try to support arbitrary objects
                except AttributeError:
                    print(item)
                    raise

                out.append(serializer(
                    transform_key=transform_key,
                    transform_value=transform_value
                ))
            return out

        # We call the single serializer
        return self._dump_python(**kwargs)

    def _dump_python(self,
                     transform_value=lambda field, value: value,
                     transform_key=  lambda x: x):
        """
        The single-object serializer. This method exists to be personalized
        by subclasses.
        """
        # Does value needs to be stored for the given field?
        def accept_value(value, field):
            # Skip defaults/blanks/nulls
            if value == field.default:
                return False
            if value is None and field.null:
                return False
            if field.blank and value == '':
                return False

            # seo_title is redundant with short_description
            if field.attname == 'seo_title':
                return value != self.short_description

            return True

        exclude_fields = self._get_serialization_fields_blacklist()
        serialized = OrderedDict({
            'model/type': '%s.%s' % (self._meta.app_label,
                                     self.__class__.__name__.lower())
        })
        serialized['id'] = self._get_serialization_id()
        for field in self._meta.concrete_fields:
            if field.attname in exclude_fields:
                continue

            # We only insert the fields whose values are different from the
            # default
            value = getattr(self, field.attname, None)
            if accept_value(value, field):
                key = transform_key(field.attname)
                serialized[key] = transform_value(field, value)

        # Include additional data in the serialized object. We first assume
        # that the extra data is a simple mapping. If that fails, we assume
        # that it is a pair of (map, index), that puts the extra data in an
        # specific place in the resulting object.
        data = self._get_serialization_extra()
        try:
            serialized.update(data)
        except TypeError:
            data, idx = data
            items = list(serialized.items())
            items, tail = items[:idx], items[idx:]
            items.extend(data.items())
            items.extend(tail)
            serialized = OrderedDict(items)
        return serialized

    def dump_yaml(self, parents=0, siblings=0, together=None):
        """
        Serialize object to a YAML string.
        """
        from codeschool import yaml

        py_dump = self.dump_python(
            parents=parents,
            siblings=siblings,
            together=together,
            transform_value=_serialize_field_yaml,
            transform_key=lambda x: x.replace('_', ' ')
        )
        if isinstance(py_dump, list):
            return ''.join('---\n' + yaml.dumps(x) for x in py_dump)
        return yaml.dumps(py_dump)

    def dump_json(self, parents=0, siblings=0, together=None):
        """
        Serialize object to a JSON string.
        """

        py_dump = self.dump_python(
            parents=parents,
            siblings=siblings,
            together=together,
            transform_value=_serialize_field_json
        )
        return json.dumps(py_dump)


# Helper functions that serializes each field in the model
BASIC_JSON_TYPES = (int, float, str, bool, type(None))
BASIC_YAML_TYPES = BASIC_JSON_TYPES + (complex, datetime, date)


def _serialize_field_to_string(field, value):
    pass


def _serialize_field_json(field, value):
    data = _serialize_field_yaml(field, value)
    if isinstance(value, BASIC_JSON_TYPES):
        return value
    return _serialize_field_to_string(field, value)


def _serialize_field_yaml(field, value):
    if isinstance(value, BASIC_YAML_TYPES):
        return value
    return _serialize_field_to_string(field, value)
