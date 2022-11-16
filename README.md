# si206_finalProject

## MET Museum of Art API, Countries Web Scraping, and Visualizations

### Original Goals

We originally planned to use the MET API which had information about specific art pieces and
also use a website called the “Watson Library Digital Collections”, which provided a more
expansive description of the art pieces. We wanted to find the number of paintings per dynasty,
time period by using these two resources.

### Goals Achieved

During our project, we changed our scope to accommodate what was available through the
MET API. The MET API did not have dynasty information for most of the artworks. However, we
found that most of the art pieces instead had an image URL attached to them. Because of this,
and our discovery of the K-Means image clustering module, we shifted our goal to find the most
common colors used in the art based on city and time period.

We scraped the most common cities from the website, and searched MET artwork from
corresponding cities from the API. From that we used the MET API to return artwork id, artwork
location, artwork image. We then used image segmentation using K-Means clustering to
recognize the most common colors in the image, and finally averaged artwork RGB values to
find the average color of the city and time-period. We ended up creating two visualizations that
serve as an interesting perspective on analyzing MET Museum artwork and how art differs per
country and how it may shift over time.
