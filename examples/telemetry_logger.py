import asyncio
import csv
import py_iracing

async def main():
    # Create a new iRacingClient
    ir = py_iracing.iRacingClient()

    # Connect to iRacing
    if not await ir.startup():
        print("iRacing not running.")
        return

    print("Connected to iRacing.")

    # Open a CSV file to write the telemetry data to
    with open('telemetry.csv', 'w', newline='') as csvfile:
        # Create a CSV writer
        writer = csv.writer(csvfile)

        # Write the header row
        writer.writerow(['Timestamp', 'Speed', 'RPM', 'Gear', 'Throttle', 'Brake'])

        try:
            while True:
                # Wait for new data
                await ir.freeze_var_buffer_latest()

                # Get the telemetry data
                timestamp = await ir.get('SessionTime')
                speed = await ir.get('Speed')
                rpm = await ir.get('RPM')
                gear = await ir.get('Gear')
                throttle = await ir.get('Throttle')
                brake = await ir.get('Brake')

                # Write the data to the CSV file
                writer.writerow([timestamp, speed, rpm, gear, throttle, brake])

                print(f"Logged data at {timestamp:.2f}s")
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    asyncio.run(main())