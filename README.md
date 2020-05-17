# Water Meter Data Utility for Kansas City Water

A simple utility that you can use to login to your KC Water account and retrieve your meter readings.

## Install

```Shell
pip install git+git://github.com/patrickjmcd/kcwater.git
```

## Usage

```python
# Import the package
from kcwater.kcwater import KCWater

kc_water = KCWater("username", "password")
kc_water.login()

# Get a list of hourly readings
hourly_data = kc_water.get_usage_hourly()

# Get a list of hourly readings
daily_data = kc_water.get_usage_daily()

logging.info("Last daily data: {}\n\n".format(daily_data[-1]))
logging.info("Last hourly data: {}\n\n".format(hourly_data[-1]))

logging.info("Last daily reading: {} gal for {}".format(daily_data[-1]["gallonsConsumption"], daily_data[-1]["readDate"]))
logging.info("Last hourly reading: {} gal for {} {}".format(hourly_data[-1]["gallonsConsumption"], hourly_data[-1]["readDate"], hourly_data[-1]["readDateTime"]))
```
