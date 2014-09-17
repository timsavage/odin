# -*- coding: utf-8 -*-


class TraversalPath(object):
    """
    A path through a resource structure.
    """
    def __init__(self, path):
        self._path = path

    def __str__(self):
        return '.'.join("%s" % f if k is None else "%s[%s]" % (f, k) for f, k in self._path)

    def __iter__(self):
        return iter(self._path)

    def is_resource(self, root_resource):
        """
        This path refers to a resource.
        """
        pass

    def is_valid(self, root_resource):
        """
        This path refers to a valid item (resource or otherwise)
        """
        pass

    def get_value(self, root_resource):
        """
        Get a value from a resource structure.
        """
        pass


class ResourceTraversalIterator(object):
    """
    Iterator for traversing (walking) a resource structure, including traversing composite fields to fully navigate a
    resource tree.

    This class has hooks that can be used by subclasses to customise the behaviour of the class:

     - *on_pre_enter* - Called prior to entering a new resource.
     - *on_enter* - Called after entering a new resource.
     - *on_exit* - Called after exiting a resource.

    """
    def __init__(self, resource):
        # Stack of resource iterators (starts initially with single entry of the root resource)
        self._resource_iters = [iter([(None, resource)])]
        # Stack of composite fields, found on each resource, each composite field is interrogated for resources.
        self._field_iters = []
        # The "path" to the current resource.
        self._path = [(None, None)]
        self._resource_stack = [None]

    def __iter__(self):
        return self

    def __next__(self):
        if self._resource_iters:
            if self._field_iters:
                # Check if the last entry in the field stack has any unprocessed fields.
                if self._field_iters[-1]:
                    # Select the very last field in the field stack.
                    field = self._field_iters[-1][-1]
                    # Request a list of resources along with keys from the composite field.
                    self._resource_iters.append(field.item_iter_from_object(self.current_resource))
                    # Update the path
                    self._path.append((field.name, None))
                    self._resource_stack.append(None)
                    # Remove the field from the list (and remove this field entry if it has been emptied)
                    self._field_iters[-1].pop()
                    if not self._field_iters[-1]:
                        self._field_iters.pop()
                else:
                    self._field_iters.pop()

            if self.current_resource:
                if hasattr(self, 'on_exit'):
                    self.on_exit()

            try:
                key, next_resource = next(self._resource_iters[-1])
            except StopIteration:
                # End of the current list of resources pop this list off and get the next list.
                self._path.pop()
                self._resource_iters.pop()
                self._resource_stack.pop()

                return next(self)
            else:
                if hasattr(self, 'on_pre_enter'):
                    self.on_pre_enter()

                # If we have a key (ie DictOf, ListOf composite fields) update the path key field.
                if key is not None:
                    field, _ = self._path[-1]
                    self._path[-1] = (field, key)

                # Get list of any composite fields for this resource (this is a cached field).
                self._field_iters.append(list(next_resource._meta.composite_fields))

                # self.current_resource = next_resource
                self._resource_stack[-1] = next_resource

                if hasattr(self, 'on_enter'):
                    self.on_enter()
                return next_resource
        else:
            raise StopIteration()

    # Python 2.x compatibility
    next = __next__

    @property
    def path(self):
        """
        Path to the current resource node in the tree structure.

        This path can be used to later traverse the tree structure to find get to the specified resource.
        """
        # The path is offset by one as the path includes the root to simplify next method.
        return TraversalPath(self._path[1:])

    @property
    def depth(self):
        """
        Depth of the current resource in the tree structure.
        """
        return len(self._path) - 1

    @property
    def current_resource(self):
        if self._resource_stack:
            return self._resource_stack[-1]
