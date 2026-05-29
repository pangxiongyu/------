from __future__ import annotations

from pathlib import Path

from src.data_io.weather_loader import WeatherMap


def plot_weather_layer(
    weather_map: WeatherMap,
    output_path: str | Path,
    time: str | None = None,
    height_m: float | None = None,
) -> None:
    import matplotlib.pyplot as plt

    layer = weather_map.layer(time=time, height_m=height_m)
    if layer.empty:
        raise ValueError("No weather layer found for plotting.")

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        layer["longitude"],
        layer["latitude"],
        c=layer["cost"],
        cmap="viridis",
        s=30,
    )
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(f"Weather cost layer time={time or 'any'} height={height_m or 'any'}")
    fig.colorbar(scatter, ax=ax, label="weather cost")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

