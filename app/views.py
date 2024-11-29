from .models import County
from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView




def county_map(request, id):
    county = County.objects.get(id=id)
    return render(
        request,
        "map.html",
        {
            "county": county,
        },
    )

class CountyGeoJSONView(GeoJSONLayerView):
    def get_queryset(self):
        return County.objects.filter(id=self.kwargs["id"])

    def render_to_response(self, context, **response_kwargs):
        county = self.get_queryset().first()
        if not county:
            print("No county found")
            return JsonResponse({"error": "county not found"}, status=404)

        try:
            
            print(f"County shape_file: {county.shape_data}")
            shape_file = (
                county.shape_data
            )  
            data = {"shape_file": shape_file} 
            return JsonResponse(data, safe=False)  
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
