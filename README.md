# Sun–Shadow Qibla Alignment Time Finder

This Python script calculates and visualizes the moments when the sun aligns with the Qibla direction for any location on Earth. It provides accurate solar alignment timings and plots a sun path diagram that highlights when a person's shadow will point directly toward or away from the Kaabah in Makkah.

---

## How to Use

1. Read Readme.md and follow instruction to install necessary module in your Python.
2. run the FindKiblat.py
3. Enter your longitude and latitude of your place.  You can use Google Maps to find out your place's longitude and latitude.
4. Press enter to use the suggested time zone.
5. Enter the date you would like to do the experiment.
6. The program provide the time to observe the sun's shadow.
7. On the date and the time, hold a stick upright making a pole and observe the pole's shadow.
8. The shadow is the way to Makkah.

--

## Features

* Custom location input (latitude and longitude)
* Automatic timezone detection (with manual override)
* Qibla bearing calculation from any point on Earth
* Sunrise and sunset time calculation using Skyfield
* High-precision sun-shadow alignment timing
* Polar plot of sun’s path with alignment markers
* Polar region support (e.g., Arctic, Antarctic)

---

## Requirements

Install the required Python packages:

```
pip install numpy matplotlib skyfield pytz timezonefinder scipy
```

---

## Usage

Run the script from the terminal:

```
python Find_Kiblat.py
```

You will be prompted to enter:

* Latitude and Longitude (with a default provided)
* Confirmation of the detected timezone (auto or manual)
* Optional date (defaults to today if left blank)

---

## What the Script Calculates

* Qibla Direction: Bearing from your location to the Kaabah (in degrees)
* Sun’s Path: Azimuth and altitude for every minute of the day
* Best Alignment Times: When the sun is aligned with or directly opposite the Qibla bearing
* Sunrise and Sunset: Local times based on the solar ephemeris

---

## Sample Console Output

```
Final Settings:
 Latitude : 3.139
 Longitude: 101.6869
 Timezone : Asia/Kuala_Lumpur

--- Sun Times ---
Sunrise (Local): 2025-06-13 07:02:12
Sunset (Local): 2025-06-13 19:23:47

--- Shadow Alignment Times ---
Alignment (Facing Qibla):
 UTC: 2025-06-13 05:42:00.123456+00:00
 Local: 2025-06-13 13:42:00.123456+08:00
 Azimuth error: 0.001234°

Alignment (Kaabah Behind):
 UTC: 2025-06-13 11:22:30.654321+00:00
 Local: 2025-06-13 19:22:30.654321+08:00
 Azimuth error: 0.003567°
```
![image](https://github.com/user-attachments/assets/e2899b26-b59c-4af5-b122-3510562ac9ff)

---

## Files

* `Find_Kiblat.py` — Main Python script
* `~/.skyfield-data/` — Automatically created directory for ephemeris data

---

## How It Works

1. Qibla Bearing is computed using the great-circle distance formula from your location to the Kaabah (lat: 21.4225, lon: 39.8262).
2. Skyfield is used to compute the sun's position (azimuth and altitude) minute-by-minute.
3. The script searches for the time(s) when the sun’s azimuth matches the Qibla bearing (± small error margin).
4. Sunrise and sunset times are used to ensure alignment occurs during daylight.
5. Matplotlib is used to generate a polar plot of the sun's path and alignment markers.

---

## Polar Region Support

If your location is within the polar circles (above 66.5°N or below 66.5°S), the script accounts for the possibility of:

* 24-hour daylight or night
* Sun never rising or setting
* Polar alignment visibility conditions

---

## Acknowledgements

* Skyfield — High-precision solar position data
* TimezoneFinder — Timezone detection from coordinates
* Matplotlib — Plotting library

---

## License

MIT License — Free to use, share, and modify. Attribution appreciated.

---

## Future Improvements

Planned or suggested enhancements:

* Export results to PDF or image
* Batch mode for multiple locations
* Moon–Qibla alignment detection
* Web or mobile UI for field use
