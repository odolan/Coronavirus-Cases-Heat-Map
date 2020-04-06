from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from datetime import datetime
import datetime as dt
import pandas as pd
import numpy as np
import gmplot

# retrieves updated counties data and returns it as pandas dataframe 
def getCountiesData(): 
    df = pd.read_csv('Counties.csv')
    return df

# retrieves updated New York Times data and returns it as pandas dataframe 
def getTimesData():
    url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    df = pd.read_csv(url)

    # format the columns in the pandas object
    df['place'] = df[['state', 'county']].agg(', '.join, axis=1)
    del df['state']
    del df['county']
    df['date'] = pd.to_datetime(df.date)  # conversts all times to dates

    mostUpdatedDay = getCurrentDay(df)

    dates = df['date'] == mostUpdatedDay
    filtered = df.loc[dates]
    df = filtered
    df.reset_index(inplace=True)
    return df

#function returns most updated data available
def getCurrentDay(dataframe):
    newestDay = dt.datetime(2019, 1, 1)
    for day in dataframe['date']:
        if day > newestDay:
            newestDay = day
    return newestDay

#returns the coordinates for any string location 
def getCords(location, geolocator):
    place = geolocator(location)
    if place:
        return place.latitude, place.longitude #returns lat and lon
    else:
        return 0, 0 #for any location that fails to return a location will be drawn at lat: 0, lon: 0 

'''no user should have to use this file'''
# run one time at the begininng to setup files (do not run after setup) this takes a few hours to run
def initializeCountiesFile():
    geolocator = Nominatim(user_agent="CoronaHeatMap")
    geolocator_timed = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    newyorktimes_data = getTimesData()

    df = pd.DataFrame(columns=['county', 'cases', 'latitude', 'longitude'])
    counter = 0
    for index, row in newyorktimes_data.iterrows():
        lat, lon = getCords(row['place'], geolocator_timed)
        df.loc[counter] = [row['place'], row['cases'], lat, lon]
        print(str((counter / len(newyorktimes_data.index)) * 100) + "% Completed. " + str(len(newyorktimes_data.index)-counter) + " left. " + str(df.loc[counter]['county']) + "data added")
        counter += 1
    df.to_csv('Counties.csv', index=False)  # saves file

# populate the county csv with updated data
def updateTimes():
    df = getTimesData() #returns pandas dataframe of new york times data

    """updates 'MostRecentDay.txt' to show the most current update """
    newestData = getCurrentDay(df)
    lastUpdatedDay = open('MostRecentDay.txt', 'r').read()
    currentDate = datetime.strptime(lastUpdatedDay, '%Y-%m-%d %X')

    if newestData > currentDate: #checks to see if there is newer data available 
        counties_data = getCountiesData()
        for index, row in counties_data.iterrows(): # if there is, all of the data is updated 
            sick_count = df.loc[df['place'] == row['county']]['cases']
            row['cases'] = sick_count  # appends sick count to row

        dateHolder = open("MostRecentDay.txt", "w")
        dateHolder.write(str(newestData))
        dateHolder.close()  # edit the txt file to show the newest date

        counties_data.to_csv('Counties.csv', index=False) #saves file

# create gmplot map (stored as html file)
def createMap():
    gmap = gmplot.GoogleMapPlotter(37.428, -95, 5) # first two params are the lat and lon of location the program loads to
                                                   # third param is how zoomed in you want the starting map
    gmap.apikey =  "API_KEY_HERE"                 

    updateTimes() #updates the data if its needed

    counties_data = getCountiesData() # grabs data from "Counties.csv" as a pandas dataframe 

    for index, row in counties_data.iterrows(): #iterates through all of the counties 
        lat, lon = row['latitude'], row['longitude'] #grabs lat and lon for each county
        cases = row['cases'] #grabs case numbers for each county

        if cases > 0:
            """comment out one of the following two size variables depending on scaling desired"""
            size = 1000 * np.log(cases*2) #more even distribution
            size = cases #actual scaling 
            
        gmap.circle(lat, lon, radius=size, color='red') #adds a circle to the map 
    gmap.draw("map.html") #saved the html map to file location 

createMap() # calls main run function 
