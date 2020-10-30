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
    """Return a JSON list of dates and tobs in the most active station for the previous year."""

    # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]
    latest_date = dt.datetime.strptime(latest_date_string, "%Y-%m-%d")

    # Calculate the date 1 year ago from the last data point in the database
    year_ago_date = latest_date - dt.timedelta(days=365)

    # Query station names and their observation counts, sort in descending order, and select most active station
    station_active = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).all()
    
    station_active_most = station_active[0][0]
       
    # Query the dates and tobs of most active station for the last year
    active_tobs_data = session.query(Measurement).\
    filter(Measurement.station == station_active_most).\
    filter(func.strftime("%Y-%m-%d", Measurement.date) >= year_ago_date).all()           
                
    # Create a JSON list of dates and tobs for the most active station
    tobs_list = []
    for result in active_tobs_data:
        tobs_dict = {}
        tobs_dict["date"] = result.date
        tobs_dict["station"] = result.station
        tobs_dict["tobs"] = result.tobs
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)


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

    # Find the latest date in the dataset
    latest_date_query = session.query(func.max(func.strftime("%Y-%m-%d", Measurement.date))).all()
    latest_date_string = latest_date_query[0][0]

    # Get the temperatures
    temps_1 = calc_temps(start, latest_date_string)

    # Create a JSON list for start_date
    return_list_1 = []
    date_dict_1 = {"start_date": start, "end_date": latest_date_string}
    return_list_1.append(date_dict_1)
    return_list_1.append({"Observation": "TMIN", "Temperature": temps_1[0][0]})
    return_list_1.append({"Observation": "TAVG", "Temperature": temps_1[0][1]})
    return_list_1.append({"Observation": "TMAX", "Temperature": temps_1[0][2]})

    return jsonify(return_list_1)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    """Return a JSON list of the minimum, average, and maximum temperatures for a given start-end range."""

    # Get the temperatures
    temps_2 = calc_temps(start, end)

    #create a list
    return_list_2 = []
    date_dict_2 = {"start_date": start, "end_date": end}
    return_list_2.append(date_dict_2)
    return_list_2.append({"Observation": "TMIN", "Temperature": temps_2[0][0]})
    return_list_2.append({"Observation": "TAVG", "Temperature": temps_2[0][1]})
    return_list_2.append({"Observation": 'TMAX', "Temperature": temps_2[0][2]})

    return jsonify(return_list_2)

if __name__ == "__main__":
    app.run(debug=True)