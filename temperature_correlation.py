#take the station and city data files in the format provided on the command line



import sys

import numpy as np
import pandas as pd


# stations = pd.read_json("stations.json.gz", lines=True)

# print(stations.head())
# print("------------------------------")
# print(stations.columns)
# print("------------------------------")
# print(stations.shape)

# print("------------------------------")
# print(stations['avg_tmax'].head())


# stations['avg_tmax'] = stations['avg_tmax'] / 10

# print("------------------------------")
# print("after dividing by 10:")
# print(stations['avg_tmax'].head())


import matplotlib.pyplot as plt


#Write a function distance(city, stations) that calculates the distance between one city and every station. You can probably adapt your function from the GPS question last week. [1]
def distance(city, stations):

    R = 6371000.0  # mean eart radius (source: https://www.mathworks.com/help/map/ref/earthradius.html)

    # 
    lat1 = np.radians(city['latitude'])
    lon1 = np.radians(city['longitude'])

    lat2 = np.radians(stations['latitude'])
    lon2 = np.radians(stations['longitude'])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2

    return 2 * R * np.arcsin(np.sqrt(a))

#Write a function best_tmax(city, stations) that returns the best value you can find for 'avg_tmax' for that one city, from the list of all weather stations. Hint: use distance and numpy.argmin (or Series.idxmin or DataFrame.idxmin) for this. [2]
def best_tmax(city, stations):

    dists = distance(city, stations)
    return stations['avg_tmax'].iloc[np.argmin(dists)]


def main():
    stations_file = sys.argv[1]
    city_data_file = sys.argv[2]
    output_file = sys.argv[3]

    stations = pd.read_json(stations_file, lines=True)
    stations['avg_tmax'] = stations['avg_tmax'] / 10  # The 'avg_tmax' column in the weather data is °C×10 (because that's what GHCN distributes): it needs to be divided by 10.

    cities = pd.read_csv(city_data_file)
    #need both population and area to compute density
    cities = cities.dropna(subset=['population', 'area'])
    cities['area'] = cities['area'] / 1000000  # from m^2 to km^2
    cities = cities[cities['area'] <= 10000]
    cities['density'] = cities['population'] / cities['area']

    cities['avg_tmax'] = cities.apply(best_tmax, axis=1, stations=stations)




    # print(cities[['name', 'density', 'avg_tmax']].head())
    # print('cities plotted:', len(cities))
    # print('tmax range:', cities['avg_tmax'].min(), cities['avg_tmax'].max())





    plt.figure()
    plt.scatter(cities['avg_tmax'], cities['density'], s=10)
    plt.title('Temperature vs Population Density')
    plt.xlabel('Avg Max Temperature (\u00b0C)')
    plt.ylabel('Population Density (people/km\u00b2)')
    plt.savefig(output_file)


main()
