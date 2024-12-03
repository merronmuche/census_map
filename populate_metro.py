# scripts/populate_metro_areas_with_cbsa.py

import os
import django
import uuid

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import MetropolitanArea


# List of top metropolitan areas with CBSA codes
metro_areas = [
    {"name": "New York–Newark–Jersey City, NY-NJ MSA", "description": "New York–Newark, NY-NJ-CT-PA CSA", "cbsa_code": "35620", "population_2023": 19498249},
    {"name": "Los Angeles–Long Beach–Anaheim, CA MSA", "description": "Los Angeles–Long Beach, CA CSA", "cbsa_code": "31080", "population_2023": 12799100},
    {"name": "Chicago–Naperville–Elgin, IL-IN-WI MSA", "description": "Chicago–Naperville, IL-IN-WI CSA", "cbsa_code": "16980", "population_2023": 9262825},
    {"name": "Dallas–Fort Worth–Arlington, TX MSA", "description": "Dallas–Fort Worth, TX-OK CSA", "cbsa_code": "19100", "population_2023": 8100037},
    {"name": "Houston–Pasadena–The Woodlands, TX MSA", "description": "Houston–Pasadena, TX CSA", "cbsa_code": "26420", "population_2023": 7510253},
    {"name": "Atlanta–Sandy Springs–Roswell, GA MSA", "description": "Atlanta–Athens-Clarke County–Sandy Springs, GA-AL CSA", "cbsa_code": "12060", "population_2023": 6307261},
    {"name": "Washington–Arlington–Alexandria, DC-VA-MD-WV MSA", "description": "Washington–Baltimore–Arlington, DC-MD-VA-WV-PA CSA", "cbsa_code": "47900", "population_2023": 6304975},
    {"name": "Philadelphia–Camden–Wilmington, PA-NJ-DE-MD MSA", "description": "Philadelphia–Reading–Camden, PA-NJ-DE-MD CSA", "cbsa_code": "37980", "population_2023": 6246160},
    {"name": "Miami–Fort Lauderdale–West Palm Beach, FL MSA", "description": "Miami–Port St. Lucie–Fort Lauderdale, FL CSA", "cbsa_code": "33100", "population_2023": 6183199},
    {"name": "Phoenix–Mesa–Chandler, AZ MSA", "description": "Phoenix–Mesa, AZ CSA", "cbsa_code": "38060", "population_2023": 5070110},
    {"name": "Boston–Cambridge–Newton, MA-NH MSA", "description": "Boston–Worcester–Providence, MA-RI-NH CSA", "cbsa_code": "14460", "population_2023": 4919179},
    {"name": "Riverside–San Bernardino–Ontario, CA MSA", "description": "Los Angeles–Long Beach, CA CSA", "cbsa_code": "40140", "population_2023": 4688053},
    {"name": "San Francisco–Oakland–Berkeley, CA MSA", "description": "San Jose–San Francisco–Oakland, CA CSA", "cbsa_code": "41860", "population_2023": 4566961},
    {"name": "Detroit–Warren–Dearborn, MI MSA", "description": "Detroit–Warren–Ann Arbor, MI CSA", "cbsa_code": "19820", "population_2023": 4342304},
    {"name": "Seattle–Tacoma–Bellevue, WA MSA", "description": "Seattle–Tacoma, WA CSA", "cbsa_code": "42660", "population_2023": 4044837},
    {"name": "Minneapolis–St. Paul–Bloomington, MN-WI MSA", "description": "Minneapolis–St. Paul, MN-WI CSA", "cbsa_code": "33460", "population_2023": 3712020},
    {"name": "Tampa–St. Petersburg–Clearwater, FL MSA", "description": "Tampa–St. Petersburg, FL CSA", "cbsa_code": "45300", "population_2023": 3342963},
    {"name": "San Diego–Chula Vista–Carlsbad, CA MSA", "description": "San Diego, CA CSA", "cbsa_code": "41740", "population_2023": 3269973},
    {"name": "Denver–Aurora–Lakewood, CO MSA", "description": "Denver–Aurora, CO CSA", "cbsa_code": "19740", "population_2023": 3005131},
    {"name": "Baltimore–Columbia–Towson, MD MSA", "description": "Washington–Baltimore–Arlington, DC-MD-VA-WV-PA CSA", "cbsa_code": "12580", "population_2023": 2834316},
    # Remaining metro areas here up to 50
    {"name": "Orlando–Kissimmee–Sanford, FL MSA", "description": "Orlando–Lakeland–Deltona, FL CSA", "cbsa_code": "36740", "population_2023": 2817933},
    {"name": "Charlotte–Concord–Gastonia, NC-SC MSA", "description": "Charlotte–Concord, NC-SC CSA", "cbsa_code": "16740", "population_2023": 2805115},
    {"name": "St. Louis, MO-IL MSA", "description": "St. Louis–St. Charles–Farmington, MO-IL CSA", "cbsa_code": "41180", "population_2023": 2796999},
    {"name": "San Antonio–New Braunfels, TX MSA", "description": "San Antonio–New Braunfels–Kerrville, TX CSA", "cbsa_code": "41700", "population_2023": 2703999},
    {"name": "Portland–Vancouver–Hillsboro, OR-WA MSA", "description": "Portland–Vancouver–Salem, OR-WA CSA", "cbsa_code": "38900", "population_2023": 2508050},
    {"name": "Austin–Round Rock–Georgetown, TX MSA", "description": "Austin–Round Rock, TX CSA", "cbsa_code": "12420", "population_2023": 2473275},
    {"name": "Pittsburgh, PA MSA", "description": "Pittsburgh–Weirton–Steubenville, PA-OH-WV CSA", "cbsa_code": "38300", "population_2023": 2422725},
    {"name": "Sacramento–Roseville–Folsom, CA MSA", "description": "Sacramento–Roseville, CA CSA", "cbsa_code": "40900", "population_2023": 2420608},
    {"name": "Las Vegas–Henderson–Paradise, NV MSA", "description": "Las Vegas–Henderson, NV CSA", "cbsa_code": "29820", "population_2023": 2336573},
    {"name": "Cincinnati, OH-KY-IN MSA", "description": "Cincinnati–Wilmington, OH-KY-IN CSA", "cbsa_code": "17140", "population_2023": 2271479},
    {"name": "Kansas City, MO-KS MSA", "description": "Kansas City–Overland Park–Kansas City, MO-KS CSA", "cbsa_code": "28140", "population_2023": 2221343},
    {"name": "Columbus, OH MSA", "description": "Columbus–Marion–Zanesville, OH CSA", "cbsa_code": "18140", "population_2023": 2180271},
    {"name": "Cleveland–Elyria, OH MSA", "description": "Cleveland–Akron–Canton, OH CSA", "cbsa_code": "17460", "population_2023": 2158932},
    {"name": "Indianapolis–Carmel–Anderson, IN MSA", "description": "Indianapolis–Carmel–Muncie, IN CSA", "cbsa_code": "26900", "population_2023": 2138468},
    {"name": "Nashville–Davidson–Murfreesboro–Franklin, TN MSA", "description": "Nashville–Davidson–Murfreesboro, TN CSA", "cbsa_code": "34980", "population_2023": 2102573},
    {"name": "San Jose–Sunnyvale–Santa Clara, CA MSA", "description": "San Jose–San Francisco–Oakland, CA CSA", "cbsa_code": "41940", "population_2023": 1945767},
    {"name": "Virginia Beach–Norfolk–Newport News, VA-NC MSA", "description": "Virginia Beach–Chesapeake, VA-NC CSA", "cbsa_code": "47260", "population_2023": 1787169},
    {"name": "Jacksonville, FL MSA", "description": "Jacksonville–Kingsland–Palatka, FL-GA CSA", "cbsa_code": "27260", "population_2023": 1713240},
    {"name": "Providence–Warwick, RI-MA MSA", "description": "Boston–Worcester–Providence, MA-RI-NH CSA", "cbsa_code": "39300", "population_2023": 1677803},
    {"name": "Milwaukee–Waukesha, WI MSA", "description": "Milwaukee–Racine–Waukesha, WI CSA", "cbsa_code": "33340", "population_2023": 1560424},
    {"name": "Raleigh–Cary, NC MSA", "description": "Raleigh–Durham–Cary, NC CSA", "cbsa_code": "39580", "population_2023": 1509231},
    {"name": "Oklahoma City, OK MSA", "description": "Oklahoma City–Shawnee, OK CSA", "cbsa_code": "36420", "population_2023": 1477926},
    {"name": "Louisville/Jefferson County, KY-IN MSA", "description": "Louisville/Jefferson County–Elizabethtown, KY-IN CSA", "cbsa_code": "31140", "population_2023": 1365557},
    {"name": "Richmond, VA MSA", "description": "Richmond, VA CSA", "cbsa_code": "40060", "population_2023": 1349732},
    {"name": "Memphis, TN-MS-AR MSA", "description": "Memphis–Clarksdale–Forrest City, TN-MS-AR CSA", "cbsa_code": "32820", "population_2023": 1335674},
    {"name": "Salt Lake City, UT MSA", "description": "Salt Lake City–Provo–Orem, UT CSA", "cbsa_code": "41620", "population_2023": 1267864},
    {"name": "Birmingham–Hoover, AL MSA", "description": "Birmingham–Cullman–Talladega, AL CSA", "cbsa_code": "13820", "population_2023": 1184290},
    {"name": "Fresno, CA MSA", "description": "Fresno–Hanford–Corcoran, CA CSA", "cbsa_code": "23420", "population_2023": 1180020},
    {"name": "Grand Rapids–Kentwood, MI MSA", "description": "Grand Rapids–Wyoming, MI CSA", "cbsa_code": "24340", "population_2023": 1162950},
    {"name": "Buffalo–Cheektowaga, NY MSA", "description": "Buffalo–Cheektowaga–Olean, NY CSA", "cbsa_code": "15380", "population_2023": 1155604},
    {"name": "Hartford–West Hartford–East Hartford, CT MSA", "description": "New Haven–Hartford–Waterbury, CT CSA", "cbsa_code": "25540", "population_2023": 1151543},
    {"name": "Tucson, AZ MSA", "description": "Tucson–Nogales, AZ CSA", "cbsa_code": "46060", "population_2023": 1063162},

]

def populate_metro_areas():
    for area in metro_areas:
        try:
            # Avoid duplicates
            obj, created = MetropolitanArea.objects.get_or_create(
                name=area["name"],
                defaults={
                    "description": area["description"],
                    "cbsa_code": area["cbsa_code"],
                    "uuid": uuid.uuid4(),
                },
            )
            if created:
                print(f"Created: {area['name']} with CBSA {area['cbsa_code']} and population {area['population_2023']}")
            else:
                print(f"Skipped: {area['name']} already exists.")
        except Exception as e:
            print(f"Error adding {area['name']}: {e}")

if __name__ == "__main__":
    populate_metro_areas()
