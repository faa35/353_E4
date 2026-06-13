import os
import pathlib
import sys
import numpy as np
import pandas as pd


def output_gpx(points, output_filename):
    """
    Output a GPX file with latitude and longitude from the points DataFrame.
    """
    from xml.dom.minidom import getDOMImplementation, parse
    xmlns = 'http://www.topografix.com/GPX/1/0'
    
    def append_trkpt(pt, trkseg, doc):
        trkpt = doc.createElement('trkpt')
        trkpt.setAttribute('lat', '%.10f' % (pt['lat']))
        trkpt.setAttribute('lon', '%.10f' % (pt['lon']))
        time = doc.createElement('time')
        time.appendChild(doc.createTextNode(pt['datetime'].strftime("%Y-%m-%dT%H:%M:%SZ")))
        trkpt.appendChild(time)
        trkseg.appendChild(trkpt)

    doc = getDOMImplementation().createDocument(None, 'gpx', None)
    trk = doc.createElement('trk')
    doc.documentElement.appendChild(trk)
    trkseg = doc.createElement('trkseg')
    trk.appendChild(trkseg)

    points.apply(append_trkpt, axis=1, trkseg=trkseg, doc=doc)

    doc.documentElement.setAttribute('xmlns', xmlns)

    with open(output_filename, 'w') as fh:
        fh.write(doc.toprettyxml(indent='  '))


def get_data(input_gpx):
    # TODO: you may use your code from exercise 3 here.

    #gonna read a gpxfile and return dataframe with timestamp, lat, lo
    from xml.dom.minidom import getDOMImplementation, parse
    xmlns = 'http://www.topografix.com/GPX/1/0'

    ns = {'gpx': xmlns}
    gps = pd.read_xml(input_gpx, xpath='.//gpx:trkpt', namespaces=ns,
                      parser='etree')[['lat', 'lon', 'time']]
    gps['timestamp'] = pd.to_datetime(gps['time'], utc=True, format='ISO8601')
    return gps[['timestamp', 'lat', 'lon']]





def main():
    input_directory = pathlib.Path(sys.argv[1])
    output_directory = pathlib.Path(sys.argv[2])
    
    accl = pd.read_json(input_directory / 'accl.ndjson.gz', lines=True, convert_dates=['timestamp'])[['timestamp', 'x']]
    gps = get_data(input_directory / 'gopro.gpx')
    phone = pd.read_csv(input_directory / 'phone.csv.gz')[['time', 'gFx', 'Bx', 'By']]

    first_time = accl['timestamp'].min()
    
    # TODO: create "combined" as described in the exercise

    #both two only depend on GoPro timestamps 
    # so bin them once 
    rounded = accl['timestamp'].dt.round('4s')
    accl_grouped = accl[['x']].groupby(rounded).aggregate(np.mean)

    rounded = gps['timestamp'].dt.round('4s')
    gps_grouped = gps[['lat', 'lon']].groupby(rounded).aggregate(np.mean)

    def correlation_for_offset(offset):
        phone = phone_for_offset(offset)
        joined = accl_grouped.join(phone[['gFx']], how='inner')
        return (joined['x'] * joined['gFx']).sum()
    
    # best_offset = 0
    # phone_test = phone.copy()
    # phone_test['timestamp'] = first_time + pd.to_timedelta(phone_test['time'] + best_offset, unit='sec')

    # phone_rounded = phone_test['timestamp'].dt.round('4s')
    # phone_grouped = phone_test[['gFx', 'Bx', 'By']].groupby(phone_rounded).aggregate(np.mean)

    def phone_for_offset(offset):
        p = phone.copy()

        p['timestamp'] = first_time + pd.to_timedelta(p['time'] + offset, unit='sec')
        phone_rounded = p['timestamp'].dt.round('4s')
        return p[['gFx', 'Bx', 'By']].groupby(phone_rounded).aggregate(np.mean)

    best_offset = None
    best_correlation = None

    for offset in np.linspace(-5.0, 5.0, 101):
        correlation = correlation_for_offset(offset)

        if best_correlation is None or correlation > best_correlation:
            best_correlation = correlation
            best_offset = offset

    # building out the combined data with the best offset
    phone_grouped = phone_for_offset(best_offset)

    combined = accl_grouped.join(gps_grouped, how='inner').join(phone_grouped, how='inner')
    combined = combined.reset_index().rename(columns={'timestamp': 'datetime'})

    print(f'Best time offset: {best_offset:.1f}')
    os.makedirs(output_directory, exist_ok=True)
    output_gpx(combined[['datetime', 'lat', 'lon']], output_directory / 'walk.gpx')
    combined[['datetime', 'Bx', 'By']].to_csv(output_directory / 'walk.csv', index=False)


main()
