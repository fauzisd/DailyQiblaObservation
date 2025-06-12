import math
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
from skyfield.api import Loader, Topos
from skyfield import almanac
from scipy.optimize import minimize_scalar
import pytz
from timezonefinder import TimezoneFinder

# Load astronomical data
load = Loader("~/.skyfield-data")
eph = load("de421.bsp")
ts = load.timescale()
sun = eph["sun"]
earth = eph["earth"]

# Kaabah coordinates in radians (fixed)
kaabah_lat = math.radians(21.4225)
kaabah_lon = math.radians(39.8262)

def geodetic_to_ecef(lat, lon):
    return np.array([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat)
    ])

def is_polar_region(lat):
    return abs(lat) > 66.5

def calculate_qibla_bearing(home_lat, home_lon):
    lat1 = math.radians(home_lat)
    lat2 = math.radians(21.4225)
    dLon = math.radians(39.8262 - home_lon)
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
    bearing_rad = math.atan2(x, y)
    return (math.degrees(bearing_rad) + 360) % 360

def find_azimuth_error(seconds_since_start, lat, lon, start_dt, target_azimuth):
    """
    For a time offset (in seconds from start_dt), compute the error between the sun's azimuth
    and the target bearing (or the reverse, target+180°). Returns 999 if the sun is below horizon.
    """
    dt = start_dt + timedelta(seconds=seconds_since_start)
    t = ts.from_datetime(dt)
    obs = (earth + Topos(latitude_degrees=lat, longitude_degrees=lon)).at(t).observe(sun).apparent()
    alt, az, _ = obs.altaz()
    if alt.degrees <= 0:
        return 999  # penalize times when the sun is below horizon
    
    # Compute direct error and reverse error
    direct_error = abs((az.degrees - target_azimuth + 180) % 360 - 180)
    reverse_target = (target_azimuth + 180) % 360
    reverse_error = abs((az.degrees - reverse_target + 180) % 360 - 180)
    return min(direct_error, reverse_error)

def find_closest_azimuth_time(lat, lon, timezone_str, date, target_azimuth, tol=5.0):
    """
    Find the time during the day when the sun's azimuth (or its reverse) is closest to target_azimuth.
    If the minimum error exceeds tol (in degrees), return None to indicate no valid alignment.
    """
    timezone = pytz.timezone(timezone_str)
    start_dt = timezone.localize(datetime.combine(date, datetime.min.time())).astimezone(pytz.utc)
    end_dt = start_dt + timedelta(days=1)
    duration = (end_dt - start_dt).total_seconds()

    result = minimize_scalar(
        find_azimuth_error,
        bounds=(0, duration), 
        method='bounded',
        args=(lat, lon, start_dt, target_azimuth),
        options={'xatol': 1}
    )
    
    if result.fun > tol:
        return None, result.fun  # no alignment within tolerance
    closest_time = start_dt + timedelta(seconds=result.x)
    return closest_time, result.fun

def altaz_to_xy(az_deg, alt_deg):
    """
    Convert azimuth and altitude to (x, y) coordinates.
    Here r = 90 - altitude so that the zenith is at r=0 and the horizon at r=90.
    """
    r = 90 - alt_deg
    az_rad = math.radians(az_deg)
    x = r * math.sin(az_rad)
    y = r * math.cos(az_rad)
    return x, y

def bearing_to_xy(bearing_deg):
    """
    Convert a bearing from north (in degrees) to an (x, y) coordinate on the horizon circle.
    """
    r = 90
    bearing_rad = math.radians(bearing_deg)
    x = r * math.sin(bearing_rad)
    y = r * math.cos(bearing_rad)
    return x, y

def get_coordinates():
    while True:
        try:
            lat = float(input("Enter latitude (default 3.1390): ") or 3.1390)
            lon = float(input("Enter longitude (default 101.6869): ") or 101.6869)
            return lat, lon
        except ValueError:
            print("❌ Invalid input. Please enter numeric values.\n")

def get_timezone(lat, lon):
    tf = TimezoneFinder()
    detected = tf.timezone_at(lat=lat, lng=lon) or "Asia/Kuala_Lumpur"
    print(f"🕒 Detected timezone: {detected}")
    if input("Use this timezone? (Y/n): ").strip().lower() in ("", "y", "yes"):
        return detected
    while True:
        tz = input("Enter a valid timezone (e.g., Asia/Tokyo): ").strip()
        if tz in pytz.all_timezones:
            return tz
        print("❌ Invalid timezone. Here's a full list:")
        print("\n".join(pytz.all_timezones), "\n")

# === Main ===
lat, lon = get_coordinates()
tz_str = get_timezone(lat, lon)

print(f"\n✅ Final Settings:\n Latitude : {lat}\n Longitude: {lon}\n Timezone : {tz_str}")

date_input = input("Enter date (YYYY-MM-DD) (default today): ")
try:
    date = datetime.strptime(date_input, "%Y-%m-%d").date() if date_input else datetime.now().date()
except:
    date = datetime.now().date()

timezone = pytz.timezone(tz_str)

# === Calculate Qibla Bearing ===
qibla_bearing = calculate_qibla_bearing(lat, lon)

# === Find Closest Alignment Times (two cases) ===
# Case 1: When facing Qibla directly
closest_time_facing, az_error_facing = find_closest_azimuth_time(lat, lon, tz_str, date, qibla_bearing)
# Case 2: When Kaabah is behind (reverse alignment)
closest_time_behind, az_error_behind = find_closest_azimuth_time(lat, lon, tz_str, date, (qibla_bearing + 180) % 360)

# Check if either candidate is valid (i.e. error within tolerance)
if closest_time_facing is None and closest_time_behind is None:
    shadow_found = False
else:
    shadow_found = True

# === Compute Sunrise and Sunset Times using Skyfield Almanac ===
observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
t0 = ts.utc(date.year, date.month, date.day, 0, 0, 0)
t1 = ts.utc(date.year, date.month, date.day, 23, 59, 59)
f = almanac.sunrise_sunset(eph, observer)
t_events, events = almanac.find_discrete(t0, t1, f)
sunrise_time = None
sunset_time = None
for t_event, ev in zip(t_events, events):
    # t_event.utc_datetime() already returns a tz-aware datetime
    dt_event = t_event.utc_datetime().astimezone(timezone)
    if ev == 1 and sunrise_time is None:
        sunrise_time = dt_event
    elif ev == 0 and sunset_time is None:
        sunset_time = dt_event

# === Calculate Sun Path for the Day ===
start_local = datetime.combine(date, datetime.min.time())
start_utc = timezone.localize(start_local).astimezone(pytz.utc)
end_utc = start_utc + timedelta(days=1)

sun_x = []
sun_y = []
step = timedelta(minutes=1)
t_iter = start_utc
while t_iter <= end_utc:
    ts_t = ts.from_datetime(t_iter)
    obs = earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
    sun_app = obs.at(ts_t).observe(sun).apparent()
    alt, az, _ = sun_app.altaz()
    if alt.degrees > 0:
        x, y = altaz_to_xy(az.degrees, alt.degrees)
        sun_x.append(x)
        sun_y.append(y)
    t_iter += step

# === Plotting Section ===
plt.figure(figsize=(8, 8))

# Draw the horizon (dashed circle; r = 90)
theta = np.linspace(0, 2 * math.pi, 360)
circle_x = 90 * np.sin(theta)
circle_y = 90 * np.cos(theta)
plt.plot(circle_x, circle_y, 'k--', label="Horizon (0° Alt)")

# Plot the sun's path
plt.plot(sun_x, sun_y, 'o-', color='orange', markersize=3, label="Sun Path")

# --- Mark sunrise and sunset (if available) in the plot ---
if sunrise_time is not None:
    t_sr = ts.from_datetime(sunrise_time)
    # Use (earth + observer) instead of observer
    obs_sr = (earth + observer).at(t_sr).observe(sun).apparent()
    alt_sr, az_sr, _ = obs_sr.altaz()
    x_sr, y_sr = altaz_to_xy(az_sr.degrees, alt_sr.degrees)
    plt.plot(x_sr, y_sr, 'y*', markersize=12, label="Sunrise")
    plt.text(x_sr + 1, y_sr + 1, sunrise_time.strftime('%H:%M:%S'), color='goldenrod', fontsize=9)
if sunset_time is not None:
    t_ss = ts.from_datetime(sunset_time)
    # Use (earth + observer) instead of observer
    obs_ss = (earth + observer).at(t_ss).observe(sun).apparent()
    alt_ss, az_ss, _ = obs_ss.altaz()
    x_ss, y_ss = altaz_to_xy(az_ss.degrees, alt_ss.degrees)
    plt.plot(x_ss, y_ss, 'c*', markersize=12, label="Sunset")
    plt.text(x_ss + 1, y_ss + 1, sunset_time.strftime('%H:%M:%S'), color='darkcyan', fontsize=9)

# Mark the shadow alignment events if found
if closest_time_facing:
    t_cf = ts.from_datetime(closest_time_facing)
    obs_cf = (earth + Topos(latitude_degrees=lat, longitude_degrees=lon)).at(t_cf).observe(sun).apparent()
    alt_cf, az_cf, _ = obs_cf.altaz()
    x_cf, y_cf = altaz_to_xy(az_cf.degrees, alt_cf.degrees)
    plt.plot(x_cf, y_cf, 'ro', markersize=8, label="Alignment (Facing Qibla)")
    time_str = closest_time_facing.astimezone(timezone).strftime('%H:%M:%S')
    plt.text(x_cf + 1, y_cf + 1, f"{time_str}", color='red', fontsize=9)

if closest_time_behind:
    t_cb = ts.from_datetime(closest_time_behind)
    obs_cb = (earth + Topos(latitude_degrees=lat, longitude_degrees=lon)).at(t_cb).observe(sun).apparent()
    alt_cb, az_cb, _ = obs_cb.altaz()
    x_cb, y_cb = altaz_to_xy(az_cb.degrees, alt_cb.degrees)
    plt.plot(x_cb, y_cb, 'mo', markersize=8, label="Alignment (Kaabah Behind)")
    time_str = closest_time_behind.astimezone(timezone).strftime('%H:%M:%S')
    plt.text(x_cb + 1, y_cb + 1, f"{time_str}", color='magenta', fontsize=9)

# Mark the home location
plt.plot(0, 0, 'bs', markersize=10, label="Home Location")

# Draw the Qibla bearing arrow
line_x, line_y = bearing_to_xy(qibla_bearing)
plt.arrow(0, 0, line_x, line_y, width=1.0, length_includes_head=True, color='green', label="Qibla Direction")
plt.text(line_x/2, line_y, f" Kaabah\n({qibla_bearing:.1f}°)", color='green', fontsize=10)

# If no valid shadow alignment was found, annotate on the plot
if not shadow_found:
    plt.text(0, -80, "No shadow alignment on this date", color='red',
             fontsize=12, ha='center')

plt.xlabel("X (East)")
plt.ylabel("Y (North)")
plt.title(f"Sun Path on {date.strftime('%Y-%m-%d')} at Home ({lat}, {lon})")
plt.legend(loc="upper right")
plt.grid(True)
plt.axis('equal')

# Use non-blocking plt.show
print("\n(Note: The plot window is blocking, close the plot window to continue running.)")
plt.show()

# === Console Output ===
print("\n--- Sun Times ---")
if sunrise_time:
    print("Sunrise (Local):", sunrise_time.strftime('%Y-%m-%d %H:%M:%S'))
else:
    print("Sunrise time not available for this date.")
if sunset_time:
    print("Sunset (Local):", sunset_time.strftime('%Y-%m-%d %H:%M:%S'))
else:
    print("Sunset time not available for this date.")

print("\n--- Shadow Alignment Times ---")
if shadow_found:
    if closest_time_facing:
        print("Alignment (Facing Qibla):")
        print(" UTC:", closest_time_facing)
        print(" Local:", closest_time_facing.astimezone(timezone))
        print(f" Azimuth error: {az_error_facing:.6f}°")
    if closest_time_behind:
        print("\nAlignment (Kaabah Behind):")
        print(" UTC:", closest_time_behind)
        print(" Local:", closest_time_behind.astimezone(timezone))
        print(f" Azimuth error: {az_error_behind:.6f}°")
else:
    print("No valid shadow alignment found on this date.")

