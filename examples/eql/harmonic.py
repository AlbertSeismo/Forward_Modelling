"""
Gridding and upward continuation
================================

Most potential field surveys gather data along scattered and uneven flight lines or
ground measurements. For a great number of applications we may need to interpolate these
data points onto a regular grid at a constant altitude. Upward-continuation is also a
routine task for smoothing, noise attenuation, source separation, etc.

Both tasks can be done simultaneously through an *equivalent layer* [Dampney1969]_. We
will use :class:`harmonica.EQLHarmonic` to estimate the coefficients of a set of point
sources (the equivalent layer) that fit the observed data. The fitted layer can then be
used to predict data values wherever we want, like on a grid at a certain altitude. The
sources for :class:`~harmonica.EQLHarmonic` in particular are placed one beneath each
data point at a constant relative depth from the elevation of the data point following
[Cooper2000]_.

The advantage of using an equivalent layer is that it takes into account the 3D nature
of the observations, not just their horizontal positions. It also allows data
uncertainty to be taken into account and noise to be suppressed though the least-squares
fitting process. The main disadvantage is the increased computational load (both in
terms of time and memory).
"""
import matplotlib.pyplot as plt
import numpy as np
import pyproj
import verde as vd
import harmonica as hm


# Fetch the sample total-field magnetic anomaly data from Rio de Janeiro
data = hm.datasets.fetch_rio_magnetic()

# Slice a smaller portion of the survey data to speed-up calculations for this example
region = [-42.35, -42.10, -22.35, -22.15]
inside = vd.inside((data.longitude, data.latitude), region)
data = data[inside]
print("Number of data points:", data.shape[0])

# Since this is a small area, we'll project our data and use Cartesian coordinates
projection = pyproj.Proj(proj="merc", lat_ts=data.latitude.mean())
easting, northing = projection(data.longitude.values, data.latitude.values)
coordinates = (easting, northing, data.altitude_m)

# Create the equivalent layer. We'll use the default point source configuration at a
# constant relative depth beneath each observation point. The damping parameter helps
# smooth the predicted data and ensure stability.
eql = hm.EQLHarmonic(relative_depth=1000, damping=10)

# Fit the layer coefficients to the observed magnetic anomaly.
eql.fit(coordinates, data.total_field_anomaly_nt)

# Evaluate the data fit by calculating an R?? score against the observed data.
# This is a measure of how well layer the fits the data NOT how good the interpolation
# will be.
print("R?? score:", eql.score(coordinates, data.total_field_anomaly_nt))

# Interpolate data on a regular grid with 400 m spacing. The interpolation requires an
# extra coordinate (upward height). By passing in 500 m, we're effectively
# upward-continuing the data (mean flight height is 200 m).
grid = eql.grid(spacing=400, data_names=["magnetic_anomaly"], extra_coords=500)

# The grid is a xarray.Dataset with values, coordinates, and metadata
print("\nGenerated grid:\n", grid)

# Plot original magnetic anomaly and the gridded and upward-continued version
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6), sharey=True)

# Get the maximum absolute value between the original and gridded data so we can use the
# same color scale for both plots and have 0 centered at the white color.
maxabs = vd.maxabs(data.total_field_anomaly_nt, grid.magnetic_anomaly.values)

ax1.set_title("Observed magnetic anomaly data")
tmp = ax1.scatter(
    easting,
    northing,
    c=data.total_field_anomaly_nt,
    s=20,
    vmin=-maxabs,
    vmax=maxabs,
    cmap="seismic",
)
plt.colorbar(tmp, ax=ax1, label="nT", pad=0.05, aspect=40, orientation="horizontal")

ax2.set_title("Gridded and upward-continued")
tmp = grid.magnetic_anomaly.plot.pcolormesh(
    ax=ax2,
    add_colorbar=False,
    add_labels=False,
    vmin=-maxabs,
    vmax=maxabs,
    cmap="seismic",
)
plt.colorbar(tmp, ax=ax2, label="nT", pad=0.05, aspect=40, orientation="horizontal")

plt.tight_layout(pad=0)
plt.show()
