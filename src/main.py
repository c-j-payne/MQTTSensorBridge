# sensor/src/main.py
import asyncio

from viam.module.module import Module
from viam.components.sensor import Sensor
from viam.resource.registry import Registry, ResourceCreatorRegistration

from ct101 import CT101

async def main():
    """This function creates and starts a new module, after adding all desired resources.
    Resources must be pre-registered. For an example, see the `__init__.py` file.
    """
    Registry.register_resource_creator(Sensor.SUBTYPE, CT101.MODEL, ResourceCreatorRegistration(CT101.new))

    module = Module.from_args()
    module.add_model_from_registry(Sensor.SUBTYPE, CT101.MODEL)
    await module.start()


if __name__ == "__main__":
    asyncio.run(main())