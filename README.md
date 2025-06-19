# py_iracing

A Python 3 implementation of the iRacing SDK.

This package allows you to get session data, live telemetry data, and broadcast messages to the iRacing simulator.

## Installation

```bash
pip install py-iracing
```

## Usage

```python
import asyncio
from py_iracing import iRacingClient

async def main():
    # Create a new iRacingClient
    ir = iRacingClient()

    # Wait for the simulator to start
    if not await ir.startup():
        print("iRacing not running.")
        return

    # Get the VarHeader for the 'Speed' variable
    speed_var_header = ir._var_headers_dict['Speed']
    
    # Get the unit for the 'Speed' variable
    speed_unit = speed_var_header.unit

    while True:
        await ir.freeze_var_buffer_latest()
        speed = await ir.get('Speed')
        print(f"Speed: {speed:.2f} {speed_unit}")
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())

## Disclaimer

A significant portion of this codebase was written with the assistance of Google's Gemini 2.5 Pro. While it has been carefully reviewed, there may still be some bugs or unexpected issues. If you encounter any problems, please open an issue on the project's GitHub page.
