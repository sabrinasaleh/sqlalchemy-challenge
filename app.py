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
    # print("Received precipitation api request.")

    # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]
    latest_date = dt.datetime.strptime(latest_date_string, "%Y-%m-%d")    

    # Calculate the date 1 year ago from the last data point in the database
    year_ago_date = latest_date - dt.timedelta(days=365)

    # Perform a query to retrieve the last 12 months of precipitation data
    year_prcp_data = session.query(func.strftime("%Y-%m-%d", Measurement.date), Measurement.prcp).\
    filter(func.strftime("%Y-%m-%d", Measurement.date) >= year_ago_date).all()
    
    # Prepare the dictionary with date as the key and prcp as the value
    results_dict = {}
    for result in year_prcp_data:
        results_dict[result[0]] = result[1]

    return jsonify(results_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""

    # print("Received station api request.")

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

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations in the most active station for the previous year."""

    # print("Received tobs api request for the most active station.")

     # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]
    latest_date = dt.datetime.strptime(latest_date_string, "%Y-%m-%d")

    # Calculate the date 1 year ago from the last data point in the database
    year_ago_date = latest_date - dt.timedelta(days=365)

    # Query station names and their observation counts sorted descending and select most active station
    station_active = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    station_active_most = station_active[0][0]
    print(station_active_most)
    
    # Query the dates and temperature observations of the most active station for the last year of data
    active_tobs_data = session.query(func.strftime("%Y-%m-%d", Measurement.date), Measurement.tobs).\
    filter(Measurement.station == station_active_most).\
    filter(func.strftime("%Y-%m-%d", Measurement.date) >= year_ago_date).all()           
                
    # Create a JSON list of tobs for the most active station
    tobs_list = []
    for result in active_tobs_data:
        tobs_dict = {}
        tobs_dict["date"] = result[1]
        tobs_dict["station"] = result[0]
        tobs_dict["tobs"] = float(result[2])
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)

# if error check with this:
    # tobs_list = []
    # for result in active_tobs_data:
    #     tobs_dict = {}
    #     tobs_dict["date"] = result.date
    #     tobs_dict["station"] = result.station
    #     tobs_dict["tobs"] = result.tobs
    #     tobs_list.append(tobs_dict)

    # return jsonify(tobs_list)

# Doug's Code:
# @app.route("/api/v1.0/stations")
# def stations():
#     """Return a list of stations."""
#     results = session.query(Station.station).all()
#     # Unravel results into a 1D array and convert to a list
#     stations = list(np.ravel(results))
#     return jsonify(stations)

#Create a function that gets minimum, average, and maximum temperatures for a range of dates
# This function called `calc_temps` will accept start date and end date in the format '%Y-%m-%d' 
# and return the minimum, average, and maximum temperatures for that range of dates
def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

@app.route("/api/v1.0/<start>")
def start(start):
    """Return a JSON list of the minimum, average, and maximum temperatures for a given start date."""

#    # print("Received start date api request.")

    # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]

    # Get the temperatures
    temps = calc_temps(start, latest_date_string)

    # Create a JSON list for start_date
    return_list = []
    date_dict = {"start_date": start, "end_date": latest_date_string}
    return_list.append(date_dict)
    return_list.append({"Observation": "TMIN", "Temperature": temps[0][0]})
    return_list.append({"Observation": "TAVG", "Temperature": temps[0][1]})
    return_list.append({"Observation": "TMAX", "Temperature": temps[0][2]})

    return jsonify(return_list)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    """Return a JSON list of the minimum, average, and maximum temperatures for a given start-end range."""

#    # print("Received start date and end date api request.")

    # Get the temperatures
    temps = calc_temps(start, end)

    #create a list
    return_list = []
    date_dict = {"start_date": start, "end_date": end}
    return_list.append(date_dict)
    return_list.append({"Observation": "TMIN", "Temperature": temps[0][0]})
    return_list.append({"Observation": "TAVG", "Temperature": temps[0][1]})
    return_list.append({"Observation": 'TMAX', "Temperature": temps[0][2]})

    return jsonify(return_list)



if __name__ == "__main__":
    app.run(debug=True)