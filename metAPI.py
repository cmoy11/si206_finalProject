import requests
import sqlite3
import os
from os.path import exists
from bs4 import BeautifulSoup
import shutil
from math import sqrt
import random
from matplotlib import image
from PIL import Image
from IPython.display import Image as CImage
from os import listdir
import csv
import matplotlib.pyplot as plt
import numpy as np

def create_database(name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+f'/{name}')
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Artwork
        (objectID INTEGER PRIMARY KEY, cityID INTEGER, artworkYearID INTEGER, imageURL STRING, color1 STRING, color2 STRING, color3 STRING)
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Cities
        (ID INTEGER PRIMARY KEY, city STRING)
        """
    )
    conn.commit()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS Years
        (ID INTEGER PRIMARY KEY, yearRange STRING)
        """
    )
    conn.commit()

    year_range = [('pre-1700',1), ('1700-1799',2), ('1800-1899',3), ('1900-present',4)]
    for tup in year_range:
        cur.execute(
            """
            INSERT OR IGNORE INTO Years (ID, yearRange)
            VALUES (?, ?)
            """, (tup[1], tup[0])
        )
        conn.commit()
    return cur, conn

def get_cities (start, end):
    url="https://worldpopulationreview.com/world-cities"
    html_content = requests.get(url).text

    soup = BeautifulSoup(html_content, "lxml")
    table = soup.find('table', class_ = "jsx-2006211681")
    rows = table.find_all('tr')

    city_dict = {}
    for row in rows[start + 1:end + 1]:
        data = row.find_all('td',)
        key = data[0].text.strip()
        value = data[1].text.strip()
        city_dict[int(key) - 1] = value
    list = [(k, v) for k, v in city_dict.items()]

    return list

def get_API(city_list, cur, conn):   
    cur.execute(
        """
        SELECT count(objectID) FROM Artwork
        """
    )
    conn.commit()
    data = cur.fetchall()
    original_length = data[0][0]
    print(original_length)
    
    for city in city_list:
        city_id = city[0]
        city_name = city[1]
            
        url = f"https://collectionapi.metmuseum.org/public/collection/v1/search?q=*&geoLocation={city_name}"
        data = requests.get(url)
        ids = data.json()['objectIDs']
        print(ids)
        if ids == None:
            print('No artwork found for this city')
            cur.execute(
            """
            INSERT OR IGNORE INTO Cities (ID, city)
            VALUES (?, ?)
            """, (int(city_id), city_name)
            )
            continue

        objects = []
        for id in ids:
            if  len(objects) == 25:
                print('25 objects reached')
                break
            resp = requests.get(f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{id}')
            
            try:
                if resp.json()['primaryImage']:
                    objects.append(resp.json())
                    print('valid response')
                else:
                    print('object does not have image url')
            except:
                print("inproperly formatted response")
                print(resp.json())
        
        for obj in objects:
            cur.execute(
                """
                SELECT count(objectID) FROM Artwork
                """
            )
            conn.commit()
            data = cur.fetchall()
            artwork_length = data[0][0]
            print(artwork_length)

            if artwork_length == original_length + 25:
                print('database addition for this run is complete')
                return(None)
            
            try:
                if int(obj['objectEndDate']) < 1700:
                    year_id = 1
                elif int(obj['objectEndDate']) < 1800:
                    year_id = 2
                elif int(obj['objectEndDate']) < 1900:
                    year_id = 3
                else:
                    year_id = 4
                
                cur.execute(
                    """
                    INSERT OR IGNORE INTO Artwork (objectID, cityID, artworkYearID, imageURL)
                    VALUES (?, ?, ?, ?)
                    """, (obj['objectID'], city_id, year_id, obj['primaryImage'])
                )
                conn.commit()
                print('added to database')
            except:
                print(f"error adding {obj['objectID']}")

        cur.execute(
            """
            INSERT OR IGNORE INTO Cities (ID, city)
            VALUES (?, ?)
            """, (int(city_id), city_name)
        )
        conn.commit()
        print('done adding to database')

def get_artwork_data(cur, conn):
    cur.execute(
        """
        SELECT Artwork.objectID, Cities.city, Years.yearRange, Artwork.imageURL, Artwork.color1
        FROM Artwork
        JOIN Cities
        ON Artwork.cityID = Cities.ID
        JOIN Years
        ON Artwork.artworkYearID = Years.ID
        """
    )
    conn.commit()
    return cur.fetchall()

def download_image(objectID, image_url):
    if not os.path.exists(f"images/{objectID}.jpg"):
        filename = f"images/{objectID}.jpg"
        r = requests.get(image_url, stream = True)
        try:
            r.raw.decode_content  = True
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            print('Image sucessfully downloaded')
        except:
            print('Image failed to download')
            print(filename)
    else:
        print('file already exists')

# The following code is copied from a Python module in development. Original source: https://github.com/curiousily/Machine-Learning-from-Scratch/blob/master/4_k_means.ipynb
class Point:
  def __init__(self, coordinates):
    self.coordinates = coordinates

class Cluster:  
  def __init__(self, center, points):
    self.center = center
    self.points = points

class KMeans:  
  def __init__(self, n_clusters, min_diff = 1):
    self.n_clusters = n_clusters
    self.min_diff = min_diff
    
  def calculate_center(self, points):    
    n_dim = len(points[0].coordinates)    
    vals = [0.0 for i in range(n_dim)]    
    for p in points:
      for i in range(n_dim):
        vals[i] += p.coordinates[i]
    coords = [(v / len(points)) for v in vals]    
    return Point(coords)
  
  def assign_points(self, clusters, points):
    plists = [[] for i in range(self.n_clusters)]

    for p in points:
      smallest_distance = float('inf')

      for i in range(self.n_clusters):
        distance = euclidean(p, clusters[i].center)
        if distance < smallest_distance:
          smallest_distance = distance
          idx = i

      plists[idx].append(p)
    
    return plists
    
  def fit(self, points):
    clusters = [Cluster(center=p, points=[p]) for p in random.sample(points, self.n_clusters)]
    
    while True:

      plists = self.assign_points(clusters, points)

      diff = 0

      for i in range(self.n_clusters):
        if not plists[i]:
          continue
        old = clusters[i]
        center = self.calculate_center(plists[i])
        new = Cluster(center, plists[i])
        clusters[i] = new
        diff = max(diff, euclidean(old.center, new.center))

      if diff < self.min_diff:
        break

    return clusters

def euclidean(p, q):
  n_dim = len(p.coordinates)
  return sqrt(sum([
      (p.coordinates[i] - q.coordinates[i]) ** 2 for i in range(n_dim)
  ]))

def get_points(image_path):
  # if running on someone else's computer, change everything before /si206_finalProject/images to their own filepath
  path = os.path.dirname(os.path.abspath(__file__))
  img = Image.open(path+"/images/"+image_path)  
  # img = Image.open(image_path)
  img.thumbnail((200, 400))
  img = img.convert("RGB")
  w, h = img.size
  
  points = []
  for count, color in img.getcolors(w * h):
    for _ in range(count):
      points.append(Point(color))
  return points

def rgb_to_hex(rgb):
  return '#%s' % ''.join(('%02x' % p for p in rgb))

def get_colors(filename, n_colors=3):
  points = get_points(filename)
  clusters = KMeans(n_clusters=n_colors).fit(points)
  clusters.sort(key=lambda c: len(c.points), reverse = True)
  rgbs = [map(int, c.center.coordinates) for c in clusters]
  initial_hex_list = list(map(rgb_to_hex, rgbs))
  return initial_hex_list
#End copied code
    
def hex_to_rgb(initial_hex_list):    
    final_rgbs = []
    for i in initial_hex_list:
        rgb = []
        r_hex = i[1:3]
        g_hex = i[3:5]
        b_hex = i[5:7]
        rgb.append(int(r_hex, 16))
        rgb.append(int(g_hex, 16))
        rgb.append(int(b_hex, 16))
        final_rgbs.append(rgb)
    return final_rgbs

def add_colors(cur, conn):
    artwork = get_artwork_data(cur, conn)

    for art in artwork:
        download_image(art[0], art[3])

    image_hex_list = []
    for a in artwork:
        try:
            object_id = a[0]
            city = a[1]
            yearRange = a[2]
            color1 = a[4]
            print(color1)
            
            if color1 != None:
                print('color already added to the database')
                cur.execute(
                    """
                    SELECT color1, color2, color3
                    FROM Artwork
                    WHERE objectID = ?
                    """, (object_id,)
                )
                conn.commit()
                tup_colors = cur.fetchall()
                colors = [tup_colors[0][0], tup_colors[0][1], tup_colors[0][2]]
            else:
                colors = get_colors(str(object_id) + '.jpg', n_colors=3)
                cur.execute(
                    """
                    UPDATE Artwork
                    SET color1  = ?, color2 = ?, color3  = ?
                    WHERE objectID = ?
                    AND color1 IS NULL
                    """, (colors[0], colors[1], colors[2], object_id)
                )
                conn.commit()
                print(colors)

            image_hex_list.append((object_id, city, yearRange, colors))
        except:
            print(f'error gathering colors from {object_id}.jpg')
            cur.execute(
                """
                DELETE FROM Artwork WHERE objectID = ?
                """, (object_id,)
            )
    return image_hex_list

# make sure this function is called after add_colors so then you won't have to all download_image again
def make_dictionary(input_colors):
    city_dict = {}
    time_period_dict = {}

    for a in input_colors:
        try:
            object_id = a[0]
            city = a[1]
            timePeriod = a[2]
            colors  = a[3]

            rgbs = hex_to_rgb(colors)

            r = 0
            g = 0
            b = 0
            for i in range(3):
                r += rgbs[i][0]
                g += rgbs[i][1]
                b += rgbs[i][2]

            avg_red = r//3
            avg_green = g//3
            avg_blue = b//3
            
            # put each value in the dictionaries
            # fill cities dictionary
            if city not in city_dict:
                city_dict[city] = {"red": avg_red, "green": avg_green, "blue": avg_blue, "num_pieces": 1}
            else:
                city_dict[city]["red"] = city_dict[city].get("red") + avg_red
                city_dict[city]["green"] = city_dict[city].get("green") + avg_green
                city_dict[city]["blue"] = city_dict[city].get("blue") + avg_blue
                city_dict[city]["num_pieces"] += 1
            
            # repeat for time period
            if timePeriod not in time_period_dict:
                time_period_dict[timePeriod] = {"red": avg_red, "green": avg_green, "blue": avg_blue, "num_pieces": 1}
            else:
                time_period_dict[timePeriod]["red"] = time_period_dict[timePeriod].get("red") + avg_red
                time_period_dict[timePeriod]["green"] = time_period_dict[timePeriod].get("green") + avg_green
                time_period_dict[timePeriod]["blue"] = time_period_dict[timePeriod].get("blue") + avg_blue
                time_period_dict[timePeriod]["num_pieces"] += 1

        except:
            print(f'MAKE DICTIONARY ERROR. error gathering colors from {object_id}.jpg')

    # go through city dictionary and calculate the average
    for city in city_dict:
        city_dict[city]["red"] = city_dict[city].get("red") // city_dict[city].get("num_pieces")
        city_dict[city]["green"] = city_dict[city].get("green") // city_dict[city].get("num_pieces")
        city_dict[city]["blue"] = city_dict[city].get("blue") // city_dict[city].get("num_pieces")
    # go through time period dictionary and calculate the average
    for time_period in time_period_dict:
        time_period_dict[time_period]["red"] = time_period_dict[time_period].get("red") // time_period_dict[time_period].get("num_pieces")
        time_period_dict[time_period]["green"] = time_period_dict[time_period].get("green") // time_period_dict[time_period].get("num_pieces")
        time_period_dict[time_period]["blue"] = time_period_dict[time_period].get("blue") // time_period_dict[time_period].get("num_pieces")
    
    return city_dict, time_period_dict

def write_csv(city_dict, time_period_dict):
    with open("met_city.csv", "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['city', 'number of pieces', 'average red value', 'average green value', 'average blue value'])
        for key in sorted(city_dict.keys(), reverse=True, key = lambda x:city_dict[x]['num_pieces']):
            city = key
            num = city_dict[key]['num_pieces']
            red = city_dict[key]['red']
            green = city_dict[key]['green']
            blue = city_dict[key]['blue']
            csvwriter.writerow([city, num, red, green, blue])

    with open("met_time.csv", "w") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['time period', 'number of pieces', 'average red value', 'average green value', 'average blue value'])

        custom_sort = ['pre-1700', '1700-1799', '1800-1899', '1900-present']
        for key in sorted(time_period_dict.keys(), key = lambda x: custom_sort.index(x)):
            time = key
            num = time_period_dict[key]['num_pieces']
            red = time_period_dict[key]['red']
            green = time_period_dict[key]['green']
            blue = time_period_dict[key]['blue']
            csvwriter.writerow([time, num, red, green, blue])

def visualize_data():
    # Cities Visualization 
    cities = []
    red_value = []
    green_value = []
    blue_value = []
    with open('met_city.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            cities.append(row[0])
            red_value.append(int(row[2]))
            green_value.append(int(row[3]))
            blue_value.append(int(row[4]))

    print(cities)
    print(red_value)

    x = np.arange(len(cities))  # the label locations
    width = 0.2  # the width of the bars

    plt.bar(x-0.2, red_value, width, color='red')
    plt.bar(x, green_value, width, color='green')
    plt.bar(x+0.2, blue_value, width, color='blue')
    plt.xticks(x, cities)
    plt.xlabel("City")
    plt.ylabel("RGB Value")
    plt.yscale("linear")
    plt.ylim(0, 255)
    plt.title('Average RGB Values in MET Artwork for Most Populated Citites')
    plt.legend(["Average Red Value", "Average Green Value", "Average Blue Value"])
    plt.tight_layout()
    plt.show()
    
    # Time Period Visualization 
    time = []
    red_value = []
    green_value = []
    blue_value = []
    with open('met_time.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)
        for row in csvreader:
            time.append(row[0])
            red_value.append(int(row[2]))
            green_value.append(int(row[3]))
            blue_value.append(int(row[4]))

    print(time)
    print(red_value)

    x = np.arange(len(time))  # the label locations
    width = 0.2  # the width of the bars

    plt.bar(x-0.2, red_value, width, color='red')
    plt.bar(x, green_value, width, color='green')
    plt.bar(x+0.2, blue_value, width, color='blue')
    plt.xticks(x, time)
    plt.xlabel("Time Period")
    plt.ylabel("RGB Value")
    plt.yscale("linear")
    plt.ylim(0, 255)
    plt.title('Average RGB Values in MET Artwork by Time Period')
    plt.legend(["Average Red Value", "Average Green Value", "Average Blue Value"])
    plt.tight_layout()
    plt.show()

def main():
    cur, conn = create_database('met.db')

    cur.execute(
        """
        SELECT count(id) FROM Cities
        """
    )
    conn.commit()
    data = cur.fetchall()
    length = data[0][0]
    print(length)

    if length < 75:
        print('length less than 75')   
        cities = get_cities(length, length+25)
        print(cities)
        get_API(cities, cur, conn)
        add_colors(cur, conn)
        print("done adding colors")
    elif length < 100:
        cities = get_cities(length, 100)
        print(cities)
        get_API(cities, cur, conn)
        add_colors(cur, conn)
        print("done adding colors")
    else:
        print('database addition is complete')
        colors = add_colors(cur, conn)
        print("done adding colors")

        city_dict, time_period_dict = make_dictionary(colors)
        print(time_period_dict)
        
        write_csv(city_dict, time_period_dict)

        visualize_data()

    print('done')

if __name__ == '__main__':
    main()