# -*- coding: utf-8 -*-


def generate_mapping_cache_name(from_obj, to_obj):
    return "%s.%s > %s.%s" % (from_obj.__module__, from_obj.__name__, to_obj.__module__, to_obj.__name__,)


class ResourceCache(object):
    # Use the Borg pattern to share state between all instances. Details at
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66531.
    __shared_state = dict(
        resources={},
        mappings={},
        field_resolvers=set(),
    )

    def __init__(self):
        self.__dict__ = self.__shared_state

    def register_resources(self, *resources):
        """Register a resource (or resources).

        :param resources: Argument list of resources to register.
        """
        for resource in resources:
            resource_name = resource._meta.resource_name.lower()
            self.resources[resource_name] = resource
            class_name = resource._meta.class_name.lower()
            if resource_name != class_name:
                self.resources[class_name] = resource

    def get_resource(self, resource_name):
        """Get a resource by name.

        :param resource_name: Name of the resource to find.
        :returns: The resource type that matches requested name (case insensitive); or :const:`None` if the requested
            name has not been registered.
        """
        return self.resources.get(resource_name.lower())

    def register_mapping(self, mapping):
        """Register a mapping

        :param mapping: Mapping object to register.
        """
        mapping_name = generate_mapping_cache_name(mapping.from_resource, mapping.to_resource)
        self.mappings[mapping_name] = mapping

    def get_mapping(self, from_obj, to_obj):
        """Get a mapping based on the from and to objects (likely to be resources).

        :param from_obj: Object to map from.
        :param to_obj: Object to map to.
        :returns: A mapping object that supports mapping from *from_obj* to *to_obj*
        :raises: KeyError if a mapping cannot be found.
        """
        mapping_name = generate_mapping_cache_name(from_obj, to_obj)
        return self.mappings[mapping_name]

    def register_field_resolver(self, resolver, base_type):
        """Register a field resolver.

        The *base_type* will also cover all subclasses.

        :param base_type: Base type for subclasses that this resolver will work with.
        :param resolver: Resolver object used to resolve subclasses of *base_type*.
        """
        self.field_resolvers.add((base_type, resolver))

    def get_field_resolver(self, obj_type):
        """Get a field resolver for an object type.

        :param obj_type: Object type to find a field resolver for.
        :return: A field resolver instance for resolving fields on *obj_type*.
        :raises: KeyError if a resolver cannot be found.
        """
        for base_type, field_resolver in self.field_resolvers:
            if issubclass(obj_type, base_type):
                return field_resolver(obj_type)
        raise KeyError('No field resolver could be found for %r' % obj_type)

cache = ResourceCache()

register_resources = cache.register_resources
get_resource = cache.get_resource

register_mapping = cache.register_mapping
get_mapping = cache.get_mapping

register_field_resolver = cache.register_field_resolver
get_field_resolver = cache.get_field_resolver
