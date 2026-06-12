import logging
from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = "batteryhealth"
CONF_SOURCE = "source"
CONF_SOC_ENTITY = "soc_entity"
CONF_POWER_ENTITY = "power_entity"
CONF_NOMINAL_CAPACITY_KWH = "nominal_capacity_kwh"
CONF_INVERT_POWER_SIGN = "invert_power_sign"
CONF_SOC_RISE_HYSTERESIS = "soc_rise_hysteresis"


async def async_setup_entry(hass, config_entry, async_add_entities):
    data = config_entry.data
    name = data.get(CONF_NAME, "Battery Health")
    soc_entity = data.get(CONF_SOC_ENTITY) or data.get(CONF_SOURCE)
    power_entity = data.get(CONF_POWER_ENTITY)
    nominal_capacity_kwh = data.get(CONF_NOMINAL_CAPACITY_KWH, 10.0)
    invert_power_sign = data.get(CONF_INVERT_POWER_SIGN, False)
    soc_rise_hysteresis = data.get(CONF_SOC_RISE_HYSTERESIS, 0.3)

    if not soc_entity:
        _LOGGER.warning("Config entry '%s' has no SOC entity configured", config_entry.entry_id)
        return

    runtime = BatteryHealthRuntime(
        hass=hass,
        name=name,
        soc_entity_id=soc_entity,
        power_entity_id=power_entity,
        nominal_capacity_kwh=nominal_capacity_kwh,
        invert_power_sign=invert_power_sign,
        soc_rise_hysteresis=soc_rise_hysteresis,
    )

    hass.data.setdefault(DOMAIN, {}).setdefault("runtimes", {})[config_entry.entry_id] = runtime

    async_add_entities(
        [
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="batteryhealth",
                metric_name="SOH Current",
                unit="%",
                icon="mdi:battery-heart-variant",
                value_getter=lambda rt: rt.soh_current,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soh_average",
                metric_name="SOH Average",
                unit="%",
                icon="mdi:chart-line-variant",
                value_getter=lambda rt: rt.soh_average,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="c_estimated_kwh",
                metric_name="C Estimated",
                unit="kWh",
                icon="mdi:battery-high",
                value_getter=lambda rt: rt.estimated_capacity_kwh,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="c_nominal_kwh",
                metric_name="C Nominal",
                unit="kWh",
                icon="mdi:battery-outline",
                value_getter=lambda rt: rt.nominal_capacity_kwh,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="discharged_energy_kwh",
                metric_name="Discharged Energy",
                unit="kWh",
                icon="mdi:counter",
                value_getter=lambda rt: rt.discharged_energy_kwh,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="discharged_energy_total_kwh",
                metric_name="Discharged Energy Total",
                unit="kWh",
                icon="mdi:counter",
                value_getter=lambda rt: rt.discharged_energy_total_kwh,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="full_charge_cycles",
                metric_name="Full Charge Cycles",
                unit=None,
                icon="mdi:battery-sync",
                value_getter=lambda rt: rt.full_charge_cycles,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soc_reference",
                metric_name="SOC Reference",
                unit="%",
                icon="mdi:battery-sync",
                value_getter=lambda rt: rt.soc_reference,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soc_drop",
                metric_name="SOC Drop",
                unit="%",
                icon="mdi:battery-arrow-down",
                value_getter=lambda rt: rt.soc_drop,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soc_current",
                metric_name="SOC Current",
                unit="%",
                icon="mdi:battery-medium",
                value_getter=lambda rt: rt.soc_value,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="power_current_w",
                metric_name="Power Current",
                unit="W",
                icon="mdi:flash",
                value_getter=lambda rt: rt.power_value,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soh_raw_percent",
                metric_name="SOH Raw",
                unit="%",
                icon="mdi:percent",
                value_getter=lambda rt: rt.raw_health_percent,
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="soh_measurements_count",
                metric_name="SOH Measurements",
                unit=None,
                icon="mdi:counter",
                value_getter=lambda rt: len(rt.soh_history),
            ),
            BatteryHealthMetricSensor(
                runtime=runtime,
                base_name=name,
                entry_id=config_entry.entry_id,
                unique_id_suffix="calculation_ready",
                metric_name="Calculation Ready",
                unit=None,
                icon="mdi:check-circle-outline",
                value_getter=lambda rt: 1 if bool(rt.power_entity_id) else 0,
            ),
        ]
    )

class BatteryHealthRuntime:
    def __init__(
        self,
        hass,
        name,
        soc_entity_id,
        power_entity_id,
        nominal_capacity_kwh,
        invert_power_sign,
        soc_rise_hysteresis,
    ):
        self._hass = hass
        self.name = name
        self.soc_entity_id = soc_entity_id
        self.power_entity_id = power_entity_id
        self.nominal_capacity_kwh = nominal_capacity_kwh
        self.invert_power_sign = invert_power_sign
        self.soc_rise_hysteresis = max(0.0, float(soc_rise_hysteresis))

        self.soc_value = None
        self.power_value = None
        self.discharged_energy_kwh = 0.0
        self.discharged_energy_total_kwh = 0.0
        self.soc_reference = None
        self.soc_min_in_section = None
        self.soc_drop = None
        self.estimated_capacity_kwh = None
        self.raw_health_percent = None
        self.soh_current = None
        self.soh_history = []
        self.last_update_utc = None

        self._missing_power_logged = False
        self._missing_soc_logged = False
        self._invalid_soc_logged = False
        self._invalid_power_logged = False

        self._listeners = set()
        self._tracked_unsub = None
        self._attached_entities = 0

    @property
    def soh_average(self):
        if not self.soh_history:
            return None
        return round(sum(self.soh_history) / len(self.soh_history), 2)

    @property
    def full_charge_cycles(self):
        if self.nominal_capacity_kwh <= 0:
            return None
        return self.discharged_energy_total_kwh / self.nominal_capacity_kwh

    @staticmethod
    def _is_unavailable_value(value):
        return str(value).strip().lower() in {"unknown", "unavailable", "none", "null", ""}

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)

        def _remove_listener() -> None:
            self._listeners.discard(listener)

        return _remove_listener

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    def reset_history(self) -> None:
        self.soh_history.clear()
        self._notify_listeners()

    def _finalize_section_measurement(self) -> None:
        if self.soc_reference is None or self.soc_min_in_section is None:
            return

        soc_drop = self.soc_reference - self.soc_min_in_section
        self.soc_drop = soc_drop

        if soc_drop > 0 and self.discharged_energy_kwh > 0 and self.nominal_capacity_kwh > 0:
            self.estimated_capacity_kwh = self.discharged_energy_kwh / (soc_drop / 100.0)
            self.raw_health_percent = (
                self.estimated_capacity_kwh / self.nominal_capacity_kwh
            ) * 100.0
            self.soh_current = round(max(0.0, self.raw_health_percent), 2)
            self.soh_history.append(self.soh_current)

    async def async_attach_entity(self) -> None:
        self._attached_entities += 1
        if self._attached_entities == 1:
            tracked_entities = [self.soc_entity_id]
            if self.power_entity_id:
                tracked_entities.append(self.power_entity_id)

            self._tracked_unsub = async_track_state_change_event(
                self._hass, tracked_entities, self._update_state
            )
            await self._update_state()

    async def async_detach_entity(self) -> None:
        self._attached_entities = max(0, self._attached_entities - 1)
        if self._attached_entities == 0 and self._tracked_unsub is not None:
            self._tracked_unsub()
            self._tracked_unsub = None

    async def _update_state(self, event=None):
        soc_state = self._hass.states.get(self.soc_entity_id)
        power_state = self._hass.states.get(self.power_entity_id) if self.power_entity_id else None
        now_utc = dt_util.utcnow()

        if soc_state is None:
            if not self._missing_soc_logged:
                _LOGGER.debug("[BatteryHealth] SOC entity '%s' not found (unavailable at startup?).", self.soc_entity_id)
                self._missing_soc_logged = True
            self.soc_value = None
            self.power_value = None
            self.soc_drop = None
            self.soh_current = None
            self.raw_health_percent = None
            self.estimated_capacity_kwh = None
            self.last_update_utc = now_utc
            self._notify_listeners()
            return

        self._missing_soc_logged = False
        try:
            if self._is_unavailable_value(soc_state.state):
                if not self._invalid_soc_logged:
                    _LOGGER.debug(
                        "[BatteryHealth] SOC entity '%s' is currently unavailable (%r).",
                        self.soc_entity_id,
                        soc_state.state,
                    )
                    self._invalid_soc_logged = True
                self.soc_value = None
                self.soc_drop = None
                self.soh_current = None
                self.raw_health_percent = None
                self.estimated_capacity_kwh = None
                self.last_update_utc = now_utc
                self._notify_listeners()
                return

            soc_value = float(soc_state.state)
            if soc_value < 0 or soc_value > 100:
                raise ValueError("SOC must be in range 0..100")
            self.soc_value = soc_value
            self._invalid_soc_logged = False
        except (ValueError, TypeError, AttributeError) as error:
            if not self._invalid_soc_logged:
                _LOGGER.warning(
                    "[BatteryHealthSensor] Invalid SOC value for '%s': %r (type: %s). Error: %s",
                    self.soc_entity_id,
                    soc_state.state,
                    type(soc_state.state),
                    error,
                )
                self._invalid_soc_logged = True
            self.soc_value = None
            self.soc_drop = None
            self.soh_current = None
            self.raw_health_percent = None
            self.estimated_capacity_kwh = None

        if not self.power_entity_id:
            if not self._missing_power_logged:
                _LOGGER.debug(
                    "[BatteryHealth] No power entity configured for '%s'. Health calculation not possible.",
                    self.name,
                )
                self._missing_power_logged = True
            self.power_value = None
        elif power_state is None:
            _LOGGER.debug("[BatteryHealthSensor] Power entity '%s' not found.", self.power_entity_id)
            self.power_value = None
        else:
            try:
                if self._is_unavailable_value(power_state.state):
                    if not self._invalid_power_logged:
                        _LOGGER.debug(
                            "[BatteryHealth] Power entity '%s' is currently unavailable (%r).",
                            self.power_entity_id,
                            power_state.state,
                        )
                        self._invalid_power_logged = True
                    self.power_value = None
                else:
                    power_value = float(power_state.state)
                    power_unit = str(power_state.attributes.get("unit_of_measurement", "W")).lower()
                    if power_unit == "kw":
                        power_value = power_value * 1000.0
                    if self.invert_power_sign:
                        power_value = -power_value
                    self.power_value = power_value
                    self._invalid_power_logged = False
            except (ValueError, TypeError, AttributeError) as error:
                if not self._invalid_power_logged:
                    _LOGGER.warning(
                        "[BatteryHealthSensor] Invalid power value for '%s': %r (type: %s). Error: %s",
                        self.power_entity_id,
                        power_state.state,
                        type(power_state.state),
                        error,
                    )
                    self._invalid_power_logged = True
                self.power_value = None

        full_charge_plateau = (
            self.soc_value is not None
            and self.soc_reference is not None
            and self.soc_value >= 99.5
            and self.soc_value >= (self.soc_reference - 0.05)
        )

        if self.last_update_utc is not None and self.power_value is not None:
            delta_hours = (now_utc - self.last_update_utc).total_seconds() / 3600.0
            if 0 < delta_hours <= 24:
                discharge_power_w = max(self.power_value, 0.0)
                if not (full_charge_plateau and discharge_power_w > 0):
                    delta_energy_kwh = (discharge_power_w / 1000.0) * delta_hours
                    self.discharged_energy_kwh += delta_energy_kwh
                    self.discharged_energy_total_kwh += delta_energy_kwh

        self.last_update_utc = now_utc

        if self.soc_value is not None:
            if self.soc_reference is None:
                self.soc_reference = self.soc_value
                self.soc_min_in_section = self.soc_value
            elif self.soc_value > (self.soc_reference + self.soc_rise_hysteresis):
                self._finalize_section_measurement()
                self.soc_reference = self.soc_value
                self.soc_min_in_section = self.soc_value
                self.discharged_energy_kwh = 0.0
            else:
                if self.soc_min_in_section is None:
                    self.soc_min_in_section = self.soc_value
                else:
                    self.soc_min_in_section = min(self.soc_min_in_section, self.soc_value)

            self.soc_drop = (
                self.soc_reference - self.soc_min_in_section
                if self.soc_reference is not None and self.soc_min_in_section is not None
                else None
            )
        else:
            self.soc_drop = None

        self._notify_listeners()


class BatteryHealthMetricSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(
        self,
        runtime,
        base_name,
        entry_id,
        unique_id_suffix,
        metric_name,
        unit,
        icon,
        value_getter,
    ):
        self._runtime = runtime
        self._value_getter = value_getter
        self._remove_listener = None
        self._attr_name = f"{base_name} {metric_name}"
        self._attr_unique_id = f"{entry_id}_{unique_id_suffix}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self):
        value = self._value_getter(self._runtime)
        if isinstance(value, float):
            return round(value, 5)
        return value

    @property
    def extra_state_attributes(self):
        return {
            "soc_entity": self._runtime.soc_entity_id,
            "power_entity": self._runtime.power_entity_id,
            "invert_power_sign": self._runtime.invert_power_sign,
            "soc_rise_hysteresis": self._runtime.soc_rise_hysteresis,
            "soh_measurements_count": len(self._runtime.soh_history),
            "raw_health_percent": self._runtime.raw_health_percent,
        }

    async def async_added_to_hass(self):
        self._remove_listener = self._runtime.add_listener(self._handle_runtime_update)
        await self._runtime.async_attach_entity()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        await self._runtime.async_detach_entity()

    @callback
    def _handle_runtime_update(self) -> None:
        self.async_write_ha_state()
