from viam.components.sensor import Sensor
from viam.resource.registry import Registry, ResourceCreatorRegistration
from .mqttsensorbridge import mqttsensorbridge

Registry.register_resource_creator(Sensor.SUBTYPE, mqttsensorbridge.MODEL, ResourceCreatorRegistration(mqttsensorbridge.new, mqttsensorbridge.validate_config))
