import sc2
from sc2.ids.unit_typeid import UnitTypeId

async def build_workers(context):
    print("building a worker")
    print(context.units(UnitTypeId.COMMANDCENTER))
    for cc in context.units(UnitTypeId.COMMANDCENTER):
        print("cc idle")
        if context.can_afford(UnitTypeId.SCV) and context.units(UnitTypeId.SCV).amount < 70:
            print("can afford")
            await context.do(cc.train(UnitTypeId.SCV))
