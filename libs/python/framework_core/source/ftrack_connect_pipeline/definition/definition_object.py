# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from collections.abc import MutableMapping, MutableSequence
import copy
import json

from ftrack_connect_pipeline import constants


class DefinitionObject(MutableMapping):
    '''Base DccObject class.'''

    def get_all(self, first=False, **kwargs):
        '''
        Return all items that match key and values from the given *kwargs*.
        If *first* is true will return only the first object that matches the
        given *kwargs*.
        '''
        # Example kwargs --> type=context, name=main
        results = []
        match = True
        for k, v in kwargs.items():
            # If key not in self or v not match to the k value jump out
            if self.mapping.get(k) != v:
                match = False
                break
        # Return the object in case is matching and first is true
        if match and first:
            return self
        # Append the object to the all matching results
        elif match:
            results.append(self)
        # Recursively iterate over all the values in case we have DefinitionList or
        # DefinitionObjects to look into them
        for v in self.mapping.values():
            if issubclass(type(v), DefinitionList) or issubclass(
                type(v), DefinitionObject
            ):
                # Call the get_all function of the current object
                result = v.get_all(first=first, **kwargs)
                if result and first:
                    return result
                if result:
                    results.extend(result)
        return results

    def get_first(self, **kwargs):
        '''
        Return first item that match key and values from the given *kwargs*.
        '''
        return self.get_all(first=True, **kwargs) or None

    def __init__(self, definition):
        '''
        Convert the given definition to a DefinitionObject
        '''
        super(DefinitionObject, self).__setattr__('mapping', {})
        self.update(definition)

    def __getattr__(self, k):
        return self.mapping[k]

    def __setattr__(self, k, value):
        self.mapping[k] = value

    def __getitem__(self, k):
        '''
        Get the value from the given *k*
        '''

        return self.mapping[k]

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*
        '''
        # If list convert to definition list
        if type(v) == list:
            v = DefinitionList(v)

        # If dictionary and valid category, convert to category object
        elif issubclass(type(v), dict):
            v = self.evaluate_item(v)
        self.mapping[k] = v

    def evaluate_item(self, item):
        '''
        Make sure item is converted to custom object if it's from a
        compatible category
        '''
        classes = dict(
            [(cls.__name__, cls) for cls in DefinitionObject.__subclasses__()]
        )
        if issubclass(type(item), dict):
            category = item.get('category')
            if category:
                if category.capitalize() in classes:
                    item = classes[category.capitalize()](item)
        return item

    def __delitem__(self, key):
        del self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __len__(self):
        return len(self.mapping)

    def __repr__(self):
        return f"{type(self).__name__}({self.mapping})"

    def __copy__(self, deep=False):
        '''Copy implementation'''
        cls = self.__class__
        data = object.__getattribute__(self, 'mapping')

        if deep:
            data = copy.deepcopy(data)

        return cls(data)

    def __deepcopy__(self, memodict={}):
        '''Deep copy implementation'''
        return self.__copy__(True)

    def copy(self):
        '''match the copy method of a dictionary'''
        return self.__copy__(False)

    def to_dict(self):
        '''Return dictionary type base on current data'''
        new_mapping = {}
        for k, v in self.mapping.items():
            if issubclass(type(v), DefinitionObject):
                v = v.to_dict()
            if issubclass(type(v), DefinitionList):
                v = v.to_list()
            new_mapping[k] = v
        return new_mapping

    def to_json(self, indent=None):
        '''Return json object of the internal mapping'''
        return json.dumps(self.to_dict(), indent=indent)


class Step(DefinitionObject):
    def __init__(self, step):
        super(Step, self).__init__(step)


class Stage(DefinitionObject):
    def __init__(self, stage):
        super(Stage, self).__init__(stage)


class Plugin(DefinitionObject):
    def __init__(self, plugin):
        super(Plugin, self).__init__(plugin)

    def __setitem__(self, k, v):
        '''
        Sets the given *v* into the given *k*
        '''
        # Convert options to options object
        if k == 'options':
            v = Options(v)
        super(Plugin, self).__setitem__(k, v)


class Options(DefinitionObject):
    def __init__(self, options):
        super(Options, self).__init__(options)


class DefinitionList(MutableSequence):
    def get_all(self, first=False, **kwargs):
        '''
        Return all items that match key and values from the given *kwargs*.
        '''
        results = []
        # Recursively iterate over all items in the internal list to check if
        # they match the kwargs
        for item in self.list:
            if issubclass(type(item), DefinitionList) or issubclass(
                type(item), DefinitionObject
            ):
                result = item.get_all(first=first, **kwargs)
                # Return the first value that matches if first is true
                if result and first:
                    return result
                elif result:
                    results.extend(result)
        return results

    def get_first(self, **kwargs):
        '''
        Return first item that match key and values from the given *kwargs*.
        '''
        return self.get_all(first=True, **kwargs) or None

    def __init__(self, iterable):
        '''
        Init the list given the *iterable* values
        '''
        # We use the category to identify the type of definition list in
        # the definition object
        self.category = None
        self.list = list()
        self.extend(iterable)

    def __len__(self):
        return len(self.list)

    def __getitem__(self, i):
        return self.list[i]

    def __delitem__(self, i):
        del self.list[i]

    def __setitem__(self, index, item):
        # evaluate item before assign it
        item = self.evaluate_item(item)
        self.list[index] = item

    def insert(self, index, item):
        '''Insert given *item* on the given *index*'''
        # evaluate item before assign it
        item = self.evaluate_item(item)
        self.list.insert(index, item)

    def append(self, item):
        '''Append given *item* on the internal list'''
        # evaluate item before assign it
        item = self.evaluate_item(item)
        self.list.append(item)

    def extend(self, items):
        '''Extend internal list with the current *items*'''
        new_iter = []
        for item in items:
            # evaluate item before assign it
            item = self.evaluate_item(item)
            new_iter.append(item)
        self.list.extend(new_iter)

    def __repr__(self):
        return f"{type(self).__name__}({self.list})"

    def to_list(self):
        '''Return dictionary type base on current data'''
        new_list = []
        for item in self.list:
            if issubclass(type(item), DefinitionObject):
                item = item.to_dict()
            if issubclass(type(item), DefinitionList):
                item = item.to_list()
            new_list.append(item)
        return new_list

    def to_json(self, indent=None):
        '''Return json object of the internal list'''
        return json.dumps(self.to_list(), indent=indent)

    def evaluate_item(self, item):
        '''
        Make sure item is converted to custom object if it's from a
        compatible category
        '''
        classes = dict(
            [(cls.__name__, cls) for cls in DefinitionObject.__subclasses__()]
        )
        if issubclass(type(item), dict):
            def_type = item.get('type')
            if def_type in constants.DEFINITION_TYPES:
                item = DefinitionObject(item)
            else:
                category = item.get('category')
                if category:
                    if category.capitalize() in classes:
                        item = classes[category.capitalize()](item)
                        # Set up the category of the list
                        self.category = category
        return item
