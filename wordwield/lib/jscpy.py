from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_args, get_origin
from enum import Enum
from datetime import datetime, date, time
import re
import json
from pydantic import BaseModel, Field, create_model

class Jscpy:
    '''
    A production-grade converter for JSON Schema to Pydantic models.
    Handles AnyOf, AllOf, OneOf including in nested structures.
    '''
    
    # Map of JSON Schema types to Python/Pydantic types
    TYPE_MAPPING = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'null': None,
        'array': List[Any],
        'object': Dict[str, Any]
    }
    
    # Map of JSON Schema formats to Python types
    FORMAT_MAPPING = {
        'date-time': datetime,
        'date': date,
        'time': time,
        'email': str,
        'uri': str,
        'uuid': str,
        'ipv4': str,
        'ipv6': str,
        'binary': bytes,
    }
    
    def __init__(self, base_class=BaseModel):
        '''
        Initialize the converter with the base class to use for created models.
        
        Args:
            base_class: A class that inherits from pydantic.BaseModel
        '''
        if not issubclass(base_class, BaseModel):
            raise ValueError('base_class must be a subclass of pydantic.BaseModel')
        self.base_class = base_class
        self.model_registry = {}  # Keep track of created models to avoid duplicate classes
        
    def convert(self, schema: Dict[str, Any], class_name: str = 'GeneratedModel') -> type:
        '''
        Convert a JSON Schema dict to a Pydantic model class.
        
        Args:
            schema: The JSON Schema dictionary
            class_name: The name for the generated class
            
        Returns:
            A Pydantic model class
        '''
        if not isinstance(schema, dict):
            raise ValueError('Schema must be a dictionary')
        
        # Create a unique key for this schema to avoid duplicates
        schema_str = json.dumps(schema, sort_keys=True)
        schema_key = f'{class_name}_{hash(schema_str)}'
        if schema_key in self.model_registry:
            return self.model_registry[schema_key]
        
        field_definitions = {}
        required_fields = schema.get('required', [])
        
        # Handle properties
        properties = schema.get('properties', {})
        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required_fields
            
            field_type, field_default = self._convert_property(
                prop_schema, 
                f'{class_name}_{prop_name.title()}'
            )
            
            # Create field with the proper metadata
            field_kwargs = {}
            
            # Add description/title if available
            if 'description' in prop_schema:
                field_kwargs['description'] = prop_schema['description']
            if 'title' in prop_schema:
                field_kwargs['title'] = prop_schema['title']
                
            # Add constraints
            for constraint in ['minimum', 'maximum', 'minLength', 'maxLength', 
                              'pattern', 'minItems', 'maxItems', 'exclusiveMinimum', 
                              'exclusiveMaximum', 'multipleOf']:
                if constraint in prop_schema:
                    # Convert JSON Schema naming to pydantic (e.g., minLength -> min_length)
                    pydantic_name = re.sub(r'([a-z])([A-Z])', r'\1_\2', constraint).lower()
                    field_kwargs[pydantic_name] = prop_schema[constraint]
            
            # Handle default values
            if 'default' in prop_schema:
                field_default = prop_schema['default']
            elif not is_required:
                field_default = None
                field_type = Optional[field_type]
                
            # Create the field
            field_definitions[prop_name] = (field_type, Field(default=field_default, **field_kwargs))
        
        # Handle additionalProperties
        if schema.get('additionalProperties', False) is not False:
            # The schema allows additional properties
            additional_props_schema = schema.get('additionalProperties', {})
            if additional_props_schema is True:  # Any type allowed
                additional_type = Any
            else:
                additional_type, _ = self._convert_property(
                    additional_props_schema, 
                    f'{class_name}_AdditionalProp'
                )
            
            # Add __additional_properties__ to the model's Config class
            model_config = {'extra': 'allow', '__additional_type__': additional_type}
        else:
            model_config = {'extra': 'forbid'}
            
        # Add schema description to the model's Config if available
        if 'description' in schema:
            model_config['schema_description'] = schema['description']
        if 'title' in schema:
            model_config['schema_title'] = schema['title']
            
        # Create the model class - we need to handle the config differently when using a base class
        if hasattr(self.base_class, 'Config'):
            # If the base class already has a Config class, create a subclass of it
            config_dict = {}
            for key, value in model_config.items():
                config_dict[key] = value
                
            # Create the model with base class, inheriting its Config
            model = create_model(
                class_name,
                __base__=self.base_class,
                **field_definitions
            )
            
            # Update the model's Config class with our additional settings
            for key, value in config_dict.items():
                setattr(model.Config, key, value)
        else:
            # If no Config in base class, we can set it directly
            model = create_model(
                class_name,
                __base__=self.base_class,
                # __config__=type('Config', (), model_config),
                **field_definitions
            )
        
        # Register the model to avoid duplicates
        self.model_registry[schema_key] = model
        
        return model
    
    def _convert_property(self, prop_schema: Dict[str, Any], class_name_base: str) -> Tuple[type, Any]:
        '''
        Convert a JSON Schema property definition to a Pydantic type and default value.
        
        Args:
            prop_schema: The property schema
            class_name_base: Base name for any generated subclasses
            
        Returns:
            Tuple of (type, default_value)
        '''
        # Handle AnyOf
        if 'anyOf' in prop_schema:
            return self._resolve_any_of(prop_schema['anyOf'], class_name_base)
        
        # Handle AllOf
        if 'allOf' in prop_schema:
            return self._resolve_all_of(prop_schema['allOf'], class_name_base)
        
        # Handle OneOf
        if 'oneOf' in prop_schema:
            return self._resolve_one_of(prop_schema['oneOf'], class_name_base)
        
        # Handle const (map to Literal)
        if 'const' in prop_schema:
            from typing import Literal
            return Literal[prop_schema['const']], prop_schema['const']
        
        # Handle enum
        if 'enum' in prop_schema:
            # Create an Enum class
            enum_values = prop_schema['enum']
            enum_name = f'{class_name_base}Enum'
            
            # Create valid Python identifiers for enum values
            enum_dict = {}
            for i, val in enumerate(enum_values):
                if isinstance(val, str) and val.isidentifier():
                    name = val
                else:
                    name = f'VALUE_{i}'
                enum_dict[name] = val
                
            enum_class = Enum(enum_name, enum_dict)
            return enum_class, None
        
        # Handle basic types
        schema_type = prop_schema.get('type')
        
        # Handle multiple types (e.g., ['string', 'null'])
        if isinstance(schema_type, list):
            sub_types = []
            has_null = False
            
            for t in schema_type:
                if t == 'null':
                    has_null = True
                    continue
                # Create a temp schema for each type and get its Python type
                sub_schema = {**prop_schema, 'type': t}
                sub_type, _ = self._convert_property(sub_schema, class_name_base)
                sub_types.append(sub_type)
                
            if not sub_types:  # Only had 'null'
                return Any, None
            elif len(sub_types) == 1 and has_null:
                return Optional[sub_types[0]], None
            else:
                if has_null:
                    sub_types.append(type(None))
                return Union[tuple(sub_types)], None
        
        # Format handling
        if schema_type == 'string' and 'format' in prop_schema:
            format_type = prop_schema['format']
            if format_type in self.FORMAT_MAPPING:
                return self.FORMAT_MAPPING[format_type], None
        
        # Basic type mapping
        if schema_type in self.TYPE_MAPPING:
            if schema_type == 'array':
                # Handle arrays
                items_schema = prop_schema.get('items', {})
                if not items_schema:
                    return List[Any], None
                    
                item_type, _ = self._convert_property(items_schema, f'{class_name_base}Item')
                return List[item_type], None
                
            elif schema_type == 'object':
                # Handle nested objects
                if 'properties' in prop_schema:
                    # Create a nested model
                    nested_model = self.convert(prop_schema, class_name_base)
                    return nested_model, None
                else:
                    # Generic dict with no specified properties
                    additional_props = prop_schema.get('additionalProperties', {})
                    if additional_props is True:
                        return Dict[str, Any], None
                    elif additional_props:
                        value_type, _ = self._convert_property(
                            additional_props, 
                            f'{class_name_base}Value'
                        )
                        return Dict[str, value_type], None
                    else:
                        return Dict[str, Any], None
            else:
                # Handle basic types
                return self.TYPE_MAPPING[schema_type], None
        
        # Default to Any for unknown types
        return Any, None
    
    def _resolve_any_of(self, schemas: List[Dict[str, Any]], class_name_base: str) -> Tuple[type, None]:
        '''
        Resolve a JSON Schema anyOf to a Pydantic Union type.
        
        Args:
            schemas: List of schemas in the anyOf
            class_name_base: Base name for generated classes
            
        Returns:
            Tuple of (type, None)
        '''
        types = []
        for i, schema in enumerate(schemas):
            t, _ = self._convert_property(schema, f'{class_name_base}_AnyOf{i}')
            types.append(t)
            
        if not types:
            return Any, None
        elif len(types) == 1:
            return types[0], None
        else:
            return Union[tuple(types)], None
    
    def _resolve_all_of(self, schemas: List[Dict[str, Any]], class_name_base: str) -> Tuple[type, None]:
        '''
        Resolve a JSON Schema allOf to a Pydantic type by merging all schemas.
        
        Args:
            schemas: List of schemas in the allOf
            class_name_base: Base name for generated classes
            
        Returns:
            Tuple of (type, None)
        '''
        # Merge all schemas
        merged_schema = {}
        for schema in schemas:
            self._merge_schemas(merged_schema, schema)
            
        # Process the merged schema
        return self._convert_property(merged_schema, class_name_base)
    
    def _merge_schemas(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        '''
        Merge two JSON schemas, with source taking precedence.
        
        Args:
            target: Target schema to merge into
            source: Source schema to merge from
        '''
        for key, value in source.items():
            if key == 'properties' and 'properties' in target:
                # Merge properties
                for prop_name, prop_schema in value.items():
                    if prop_name in target['properties']:
                        # Recursively merge property schemas
                        self._merge_schemas(target['properties'][prop_name], prop_schema)
                    else:
                        target['properties'][prop_name] = prop_schema
            elif key == 'required' and 'required' in target:
                # Combine required fields
                target['required'] = list(set(target['required']) | set(value))
            elif key == 'type' and 'type' in target:
                # Handle type conflicts
                if isinstance(target['type'], list) and isinstance(value, list):
                    # Intersection of types
                    target['type'] = list(set(target['type']) & set(value))
                elif isinstance(target['type'], list):
                    if value in target['type']:
                        target['type'] = value
                    else:
                        # No common type, this will likely fail validation
                        target['type'] = 'object'  # Default to object
                elif isinstance(value, list):
                    if target['type'] in value:
                        pass  # Keep target type
                    else:
                        # No common type
                        target['type'] = 'object'  # Default to object
                elif target['type'] != value:
                    # Type conflict, default to object
                    target['type'] = 'object'
            else:
                # For other fields, source takes precedence
                target[key] = value
    
    def _resolve_one_of(self, schemas: List[Dict[str, Any]], class_name_base: str) -> Tuple[type, None]:
        '''
        Resolve a JSON Schema oneOf to a Pydantic Union type.
        
        Args:
            schemas: List of schemas in the oneOf
            class_name_base: Base name for generated classes
            
        Returns:
            Tuple of (type, None)
        '''
        # For Pydantic type annotation purposes, oneOf is similar to anyOf
        return self._resolve_any_of(schemas, class_name_base)


# Helper function for easy use
def jscpy(
	schema               : Dict[str, Any],
	base_class           : BaseModel = BaseModel,
	class_name           : str = 'GeneratedModel',
	register_in_globals  : Optional[dict] = None
) -> type:
	'''
	Convert a JSON Schema to a Pydantic model with clean name and optional registration.

	Args:
		schema: JSON Schema dictionary
		base_class: Base class for the model (must inherit from BaseModel)
		class_name: Name for the generated model class
		register_in_globals: Optional dict where to register the class (e.g. globals())

	Returns:
		A Pydantic model class with explicit __name__ set.
	'''
	converter = Jscpy(base_class=base_class)
	model     = converter.convert(schema, class_name=class_name)
	model.__name__ = class_name  # ✅ Чистое имя для repr(), str(), logs()

	if register_in_globals is not None:
		register_in_globals[class_name] = model  # ✅ Зарегистрировать в globals()

	return model

