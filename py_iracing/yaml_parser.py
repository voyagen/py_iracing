import yaml
from typing import Any, Type
from yaml.reader import Reader as YamlReader

try:
    from yaml.cyaml import CSafeLoader as YamlSafeLoader
except ImportError:
    from yaml import SafeLoader as YamlSafeLoader

# https://stackoverflow.com/a/37958106/1034242
class CustomYamlSafeLoader(YamlSafeLoader):
    @classmethod
    def remove_implicit_resolver(cls: Type['CustomYamlSafeLoader'], tag_to_remove: str) -> None:
        if 'yaml_implicit_resolvers' not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()
        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [(tag, regexp) for tag, regexp in mappings if tag != tag_to_remove]

CustomYamlSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')