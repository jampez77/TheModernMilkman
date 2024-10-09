"""The Modern Milkman sensor platform."""

from datetime import date
from typing import Any
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONF_WASTAGE,
    CONF_BOTTLESSAVED,
    DOMAIN,
    CONF_NEXT_DELIVERY,
    CONF_DELIVERYDATE,
    CONF_UNKNOWN,
)
from .coordinator import TMMCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry created in the integrations UI."""

    config = hass.data[DOMAIN][entry.entry_id]
    if entry.options:
        config.update(entry.options)

    if entry.data:
        session = async_get_clientsession(hass)

        coordinator = TMMCoordinator(hass, session, entry.data)

        await coordinator.async_config_entry_first_refresh()

        wastage_sensor = TMMWastageSensor(coordinator, entry.title)
        next_delivery_sensor = TMMNextDeliverySensor(coordinator, entry.title)

        sensors = [wastage_sensor, next_delivery_sensor]
        for sensor in sensors:
            hass.data[DOMAIN][sensor.unique_id] = sensor

        async_add_entities(sensors, update_before_add=True)


class TMMNextDeliverySensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Define The Modern Milkman next delivery sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}")},
            manufacturer="The Modern Milkman",
            model="Milkround",
            name=name,
            configuration_url="https://github.com/jampez77/TheModernMilkman/",
        )
        self.data = coordinator.data.get(CONF_NEXT_DELIVERY)
        sensor_id = f"{DOMAIN}_next_delivery".lower()
        # Set the unique ID based on domain, name, and sensor type
        self._attr_unique_id = f"{DOMAIN}-{name}-next_delivery".lower()
        self.entity_id = "sensor.themodernmilkman_next_delivery"

        self.device_class = SensorDeviceClass.DATE
        if self.data == CONF_UNKNOWN:
            self.device_class = None

        self.entity_description = SensorEntityDescription(
            key="themodernmilkman_next_delivery",
            name="Next Delivery",
            icon="mdi:truck-delivery",
            device_class=self.device_class,
        )
        self._name = self.entity_description.name
        self._sensor_id = sensor_id
        self.attrs: dict[str, Any] = {}
        self._available = True
        self._attr_force_update = True
        self._attr_icon = self.entity_description.icon
        self._state = self.get_state()

    def update_from_coordinator(self):
        """Update sensor state and attributes from coordinator data."""

        self._state = self.get_state()

        attributes = {}

        if self.data is not None and self.data != CONF_UNKNOWN:
            for key, value in self.data.items():
                if isinstance(value, dict):
                    attributes.update({f"{key}_{k}": v for k, v in value.items()})
                else:
                    attributes[key] = value

        self.attrs = attributes

    def get_state(self) -> str | date:
        """Get entity state."""
        if self.data == CONF_UNKNOWN:
            return CONF_UNKNOWN

        return datetime.fromisoformat(self.data[CONF_DELIVERYDATE]).date()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update_from_coordinator()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle adding to Home Assistant."""
        await super().async_added_to_hass()
        await self.async_update()

    @property
    def name(self) -> str:
        """Process name."""
        return self._name

    async def update_parcel(self) -> None:
        """Safely update the name of the entity."""
        await self.coordinator.async_request_refresh()

        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success and self.data is not None

    @property
    def icon(self) -> str:
        """Return a representative icon of the timer."""
        return self._attr_icon

    @property
    def native_value(self) -> str | date | None:
        """Native value."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Define entity attributes."""
        return self.attrs


class TMMWastageSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """Define The Modern Milkman wastage sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}")},
            manufacturer="The Modern Milkman",
            model="Milkround",
            name=name,
            configuration_url="https://github.com/jampez77/TheModernMilkman/",
        )
        self.data = coordinator.data.get(CONF_WASTAGE)
        sensor_id = f"{DOMAIN}_wastage".lower()
        # Set the unique ID based on domain, name, and sensor type
        self._attr_unique_id = f"{DOMAIN}-{name}-wastage".lower()
        self.entity_id = "sensor.themodernmilkman_wastage"
        self.entity_description = SensorEntityDescription(
            key="themodernmilkman_wastage",
            name="Wastage",
            icon="mdi:recycle",
        )
        self._name = self.entity_description.name
        self._sensor_id = sensor_id
        self.attrs: dict[str, Any] = {}
        self._available = True
        self._attr_force_update = True
        self._attr_icon = self.entity_description.icon
        self._state = self.data[CONF_BOTTLESSAVED]

    def update_from_coordinator(self):
        """Update sensor state and attributes from coordinator data."""

        self._state = self.data[CONF_BOTTLESSAVED]

        attributes = {}

        for key, value in self.data.items():
            if isinstance(value, dict):
                attributes.update({f"{key}_{k}": v for k, v in value.items()})
            else:
                attributes[key] = value

        self.attrs = attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update_from_coordinator()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle adding to Home Assistant."""
        await super().async_added_to_hass()
        await self.async_update()

    @property
    def name(self) -> str:
        """Process name."""
        return self._name

    async def update_parcel(self) -> None:
        """Safely update the name of the entity."""
        await self.coordinator.async_request_refresh()

        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self.coordinator.last_update_success and self.data is not None

    @property
    def icon(self) -> str:
        """Return a representative icon of the timer."""
        return self._attr_icon

    @property
    def native_value(self) -> str | date | None:
        """Native value."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Define entity attributes."""
        return self.attrs
