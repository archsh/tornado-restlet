
## JSON Serialization: application/json
JSON_EXAMPLE = """
{
    "__ref": "http://api.example.com/v1/person?__limit=50&age__gt=18&__include_fields=fullname,age,gender",
    "objects": [{"fullname": "AAAA", "age": 19, "gender": "Female"},
                {},
                {}],
    "__count": 50,
    "__total": 5000,
    "__begin": 0,
    "__model": "Person"
}
"""

## YAML Serialization: application/x-yaml
YAML_EXAMPLE = """
__ref: http://api.example.com/v1/person?__limit=50&age__gt=18&__include_fields=fullname,age,gender
objects:
    - fullname: AAAA
      age: 19
      gender: Female
    - fullname: ...
    -
__count: 50,
__total: 5000,
__begin: 0,
__model: Person
"""