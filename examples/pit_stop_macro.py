import asyncio
import py_iracing

async def main():
    # Create a new iRacingClient
    ir = py_iracing.iRacingClient()

    # Connect to iRacing
    if not await ir.startup():
        print("iRacing not running.")
        return

    print("Connected to iRacing.")

    on_pit_road = False

    try:
        while True:
            # Wait for new data
            await ir.freeze_var_buffer_latest()

            # Check if we are on pit road
            if await ir.get('OnPitRoad') and not on_pit_road:
                on_pit_road = True
                print("On pit road, requesting new tires and fuel.")

                # Request new tires
                ir.pit_command(py_iracing.PitCommandMode.lf)
                ir.pit_command(py_iracing.PitCommandMode.rf)
                ir.pit_command(py_iracing.PitCommandMode.lr)
                ir.pit_command(py_iracing.PitCommandMode.rr)

                # Request a full tank of fuel
                ir.pit_command(py_iracing.PitCommandMode.fuel, 100)

            elif not await ir.get('OnPitRoad') and on_pit_road:
                on_pit_road = False
                print("Left pit road.")

            await asyncio.sleep(0.1)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(main())