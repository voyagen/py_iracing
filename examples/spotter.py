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

    try:
        while True:
            # Wait for new data
            await ir.freeze_var_buffer_latest()

            # Get the player's car index
            player_car_idx = await ir.get('PlayerCarIdx')

            # Get the positions of all cars
            car_idx_positions = await ir.get('CarIdxPosition')

            # Find the player's position
            player_pos = -1
            for i, car_idx in enumerate(car_idx_positions):
                if car_idx == player_car_idx:
                    player_pos = i
                    break

            # Get the car ahead and behind the player
            car_ahead_idx = -1
            if player_pos > 0:
                car_ahead_idx = car_idx_positions[player_pos - 1]

            car_behind_idx = -1
            if player_pos < len(car_idx_positions) - 1:
                car_behind_idx = car_idx_positions[player_pos + 1]

            # Get the driver info
            driver_info = await ir.get('DriverInfo')
            if driver_info:
                player_driver = driver_info['Drivers'][player_car_idx]
                print(f"Player: {player_driver['UserName']}")

                if car_ahead_idx != -1:
                    car_ahead_driver = driver_info['Drivers'][car_ahead_idx]
                    print(f"Car Ahead: {car_ahead_driver['UserName']}")

                if car_behind_idx != -1:
                    car_behind_driver = driver_info['Drivers'][car_behind_idx]
                    print(f"Car Behind: {car_behind_driver['UserName']}")

            print("-" * 20)
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(main())