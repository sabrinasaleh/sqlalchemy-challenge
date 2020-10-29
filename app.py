#Dependencies
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt

# Create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create session 
session = Session(engine)

# Flask Setup
app = Flask(__name__)

@app.route("/")
def main():
    """List all routes that are available."""
    return (
        f"List of Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a JSON representation of a dictionary where date is the key and precipitation is the value"""
#     print("Received precipitation api request.")

    # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]
    latest_date = dt.datetime.strptime(latest_date_string, "%Y-%m-%d")

    # Calculate the date 1 year ago from the last data point in the database
    year_ago_date = latest_date - dt.timedelta(days=365)

    # Perform a query to retrieve the last 12 months of precipitation data
    year_prcp_data = session.query(func.strftime("%Y-%m-%d", Measurement.date), Measurement.prcp).filter(func.strftime("%Y-%m-%d", Measurement.date) >= year_ago_date).all()
    
    # Prepare the dictionary with date as the key and prcp as the value
    results_dict = {}
    for result in year_prcp_data:
        results_dict[result[0]] = result[1]

    return jsonify(results_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""

#     print("Received station api request.")

    # Conduct query for the stations
    stations_data = session.query(Station).all()

    # Create a JSON list of stations
    stations_list = []
    for station in stations_data:
        station_dict = {}
        station_dict["id"] = station.id
        station_dict["station"] = station.station
        station_dict["name"] = station.name
        station_dict["latitude"] = station.latitude
        station_dict["longitude"] = station.longitude
        station_dict["elevation"] = station.elevation
        stations_list.append(station_dict)

    return jsonify(stations_list)


if __name__ == "__main__":
    app.run(debug=True)