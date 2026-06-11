<<<<<<< HEAD
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from . import DOMAIN

CONF_SOC_ENTITY = "soc_entity"
CONF_POWER_ENTITY = "power_entity"
CONF_NOMINAL_CAPACITY_KWH = "nominal_capacity_kwh"
CONF_INVERT_POWER_SIGN = "invert_power_sign"

class BatteryHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BatteryHealth."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate that selected entities exist and have correct device class
            soc_entity = user_input.get(CONF_SOC_ENTITY)
            power_entity = user_input.get(CONF_POWER_ENTITY)
            nominal_capacity = user_input.get(CONF_NOMINAL_CAPACITY_KWH, 10.0)
            
            # Check if entities exist
            if soc_entity and self.hass.states.get(soc_entity) is None:
                errors[CONF_SOC_ENTITY] = "entity_not_found"
            
            if power_entity and self.hass.states.get(power_entity) is None:
                errors[CONF_POWER_ENTITY] = "entity_not_found"
            
            # Check nominal capacity validity
            if nominal_capacity <= 0:
                errors[CONF_NOMINAL_CAPACITY_KWH] = "invalid_capacity"
            
            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        
        # Build list of available sensor entities for display
        soc_state = user_input.get(CONF_SOC_ENTITY) if user_input else None
        power_state = user_input.get(CONF_POWER_ENTITY) if user_input else None
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Battery Health"): str,
                vol.Required(CONF_SOC_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], device_class=["battery"])
                ),
                vol.Required(CONF_POWER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], device_class=["power"])
                ),
                vol.Required(CONF_NOMINAL_CAPACITY_KWH, default=10.0): vol.Coerce(float),
                vol.Optional(CONF_INVERT_POWER_SIGN, default=False): bool,
            }),
            errors=errors,
            description_placeholders={
                "soc_entity_current": f"SOC: {self.hass.states.get(soc_state).state if soc_state and self.hass.states.get(soc_state) else 'n/a'}",
                "power_entity_current": f"Power: {self.hass.states.get(power_state).state if power_state and self.hass.states.get(power_state) else 'n/a'} {self.hass.states.get(power_state).attributes.get('unit_of_measurement', '') if power_state and self.hass.states.get(power_state) else ''}",
            },
        )
=======
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from . import DOMAIN

CONF_SOC_ENTITY = "soc_entity"
CONF_POWER_ENTITY = "power_entity"
CONF_NOMINAL_CAPACITY_KWH = "nominal_capacity_kwh"
CONF_INVERT_POWER_SIGN = "invert_power_sign"

class BatteryHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BatteryHealth."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate that selected entities exist and have correct device class
            soc_entity = user_input.get(CONF_SOC_ENTITY)
            power_entity = user_input.get(CONF_POWER_ENTITY)
            nominal_capacity = user_input.get(CONF_NOMINAL_CAPACITY_KWH, 10.0)
            
            # Check if entities exist
            if soc_entity and self.hass.states.get(soc_entity) is None:
                errors[CONF_SOC_ENTITY] = "entity_not_found"
            
            if power_entity and self.hass.states.get(power_entity) is None:
                errors[CONF_POWER_ENTITY] = "entity_not_found"
            
            # Check nominal capacity validity
            if nominal_capacity <= 0:
                errors[CONF_NOMINAL_CAPACITY_KWH] = "invalid_capacity"
            
            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        
        # Build list of available sensor entities for display
        soc_state = user_input.get(CONF_SOC_ENTITY) if user_input else None
        power_state = user_input.get(CONF_POWER_ENTITY) if user_input else None
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Battery Health"): str,
                vol.Required(CONF_SOC_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], device_class=["battery"])
                ),
                vol.Required(CONF_POWER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"], device_class=["power"])
                ),
                vol.Required(CONF_NOMINAL_CAPACITY_KWH, default=10.0): vol.Coerce(float),
                vol.Optional(CONF_INVERT_POWER_SIGN, default=False): bool,
            }),
            errors=errors,
            description_placeholders={
                "soc_entity_current": f"SOC: {self.hass.states.get(soc_state).state if soc_state and self.hass.states.get(soc_state) else 'n/a'}",
                "power_entity_current": f"Power: {self.hass.states.get(power_state).state if power_state and self.hass.states.get(power_state) else 'n/a'} {self.hass.states.get(power_state).attributes.get('unit_of_measurement', '') if power_state and self.hass.states.get(power_state) else ''}",
            },
        )
>>>>>>> 24f5369 (Initial release: BatteryHealth custom component)
