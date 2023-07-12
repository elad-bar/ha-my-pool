import json

from custom_components.my_pool.common.entity_descriptions import (
    DEFAULT_ENTITY_DESCRIPTIONS,
)
from homeassistant.util import slugify

entities = {}

for entity_description in DEFAULT_ENTITY_DESCRIPTIONS:
    if entity_description.platform not in entities:
        entities[entity_description.platform] = {}

    entities[entity_description.platform][slugify(entity_description.key)] = {
        "name": slugify(entity_description.key)
    }

print(json.dumps(entities, indent=4))
