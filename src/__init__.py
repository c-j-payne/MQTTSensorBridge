from viam.components.sensor import Sensor
from viam.resource.registry import Registry, ResourceCreatorRegistration
from .ct101 import ct101


#from previous module: 
Registry.register_resource_creator(Sensor.SUBTYPE, ct101.MODEL, ResourceCreatorRegistration(ct101.new, ct101.validate_config))
