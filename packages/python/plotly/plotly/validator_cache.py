import importlib
import re
from _plotly_utils.basevalidators import LiteralValidator, SubplotidValidator


class ValidatorCache(object):
    _cache = {}

    @staticmethod
    def get_validator(parent_path, prop_name):

        key = (parent_path, prop_name)
        if key not in ValidatorCache._cache:

            # Security validation: ensure parent_path is a valid plotly validator path
            if not isinstance(parent_path, str):
                raise ValueError(f"parent_path must be string, got {type(parent_path)}")

            # Reject dangerous characters that could break import paths
            dangerous_chars = ['..', '/', '\\', ':', ';', '|', '&', '$', '`']
            if any(char in parent_path for char in dangerous_chars):
                raise ValueError(f"Invalid parent_path: {parent_path!r}")

            # Validate path format - should only contain alphanumeric, underscore, and dot
            path_pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$'
            if not re.match(path_pattern, parent_path):
                raise ValueError(
                    f"Invalid parent_path format: {parent_path!r}"
                )

            # Validate prop_name format
            if not isinstance(prop_name, str):
                raise ValueError(f"prop_name must be string, got {type(prop_name)}")
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', prop_name):
                raise ValueError(f"Invalid prop_name format: {prop_name!r}")

            if "." not in parent_path and prop_name == "type":
                # Special case for .type property of traces
                validator = LiteralValidator("type", parent_path, parent_path)
            else:
                lookup_name = None
                if parent_path == "layout":
                    from .graph_objects import Layout

                    match = Layout._subplotid_prop_re.fullmatch(prop_name)
                    if match:
                        lookup_name = match.group(1)

                lookup_name = lookup_name or prop_name
                if lookup_name == "type":
                    validator = LiteralValidator("type", parent_path, parent_path)
                elif lookup_name == "subplotid":
                    validator = SubplotidValidator("subplotid", parent_path)
                else:
                    class_name = lookup_name.title() + "Validator"
                    validator = getattr(
                        importlib.import_module("plotly.validators." + parent_path),
                        class_name,
                    )(plotly_name=prop_name)
            ValidatorCache._cache[key] = validator

        return ValidatorCache._cache[key]
