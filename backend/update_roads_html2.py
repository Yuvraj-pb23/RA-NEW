with open('templates/dashboard/roads/list.html', 'r') as f:
    content = f.read()

# I want to inject extra_css
css = """
{% block extra_head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
<style>
.leaflet-container { z-index: 1; }
</style>
{% endblock %}
"""

# replace layout
new_layout = """
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6 mt-4">
    
    <!-- Left panel: Filters & List -->
    <div class="lg:col-span-1 flex flex-col gap-4">
"""
content = content.replace('{% block page_title %}Roads{% endblock %}', 
                          '{% block page_title %}Roads{% endblock %}\n' + css)

content = content.replace('  <!-- Filters -->', new_layout + '  <!-- Filters -->', 1)

end_of_left = """
    </div>

    <!-- Right panel: Map & Details -->
    <div class="lg:col-span-2 flex flex-col gap-4">
      <div class="card p-4 h-full flex flex-col">
          <h2 class="text-base font-semibold text-slate-800 mb-2">Road Map View</h2>
          <div id="map" class="w-full h-[500px] flex-1 bg-slate-100 rounded-xl mb-4 border border-slate-200" style="min-height: 400px;"></div>
          
          <div x-show="selectedRoadInfo" class="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200" x-cloak>
              <h3 class="text-md font-bold text-slate-800" x-text="selectedRoadInfo?.name"></h3>
              <div class="grid grid-cols-2 gap-4 mt-2 text-sm">
                  <div>
                      <span class="text-slate-500 block text-xs">Project</span>
                      <span class="font-medium text-slate-700" x-text="selectedRoadInfo?.project_name || '-'"></span>
                  </div>
                  <div>
                      <span class="text-slate-500 block text-xs">Road Type</span>
                      <span class="font-medium text-slate-700" x-text="selectedRoadInfo?.road_type_display || '-'"></span>
                  </div>
                  <div>
                      <span class="text-slate-500 block text-xs">Length</span>
                      <span class="font-medium text-slate-700"><span x-text="selectedRoadInfo?.length ? parseFloat(selectedRoadInfo.length).toFixed(3) : '-'"></span> km</span>
                  </div>
                  <div>
                      <span class="text-slate-500 block text-xs">Organization</span>
                      <span class="font-medium text-slate-700" x-text="selectedRoadInfo?.organization_name || '-'"></span>
                  </div>
              </div>
          </div>
      </div>
    </div>
  </div>
"""

content = content.replace('  <!-- Create/Edit Modal -->', end_of_left + '\n  <!-- Create/Edit Modal -->', 1)

table_row_old = '<tr class="hover:bg-slate-50 transition-colors">'
# Use single quotes properly to avoid double escaping problems when rendering or clicking using alpine attributes
table_row_new = '<tr class="hover:bg-slate-50 transition-colors cursor-pointer" @click="selectRoad(road)" :class="(selectedRoadInfo && selectedRoadInfo.id === road.id) ? \'bg-indigo-50/50\' : \'\'">'
content = content.replace(table_row_old, table_row_new)

actions_old = '<div class="flex items-center justify-end gap-1.5">'
actions_new = '<div class="flex items-center justify-end gap-1.5" @click.stop>'
content = content.replace(actions_old, actions_new)

inject_script = """
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
let leafletMap = null;
let currentPolyline = null;

function initMap() {
    if (!leafletMap) {
        leafletMap = L.map('map').setView([28.6, 77.2], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(leafletMap);
    }
}

function loadGPXData(roadId) {
    initMap();
    fetch(`/api/road/${roadId}/gpx/`)
        .then(res => {
            if (!res.ok) throw new Error('No GPX data');
            return res.json();
        })
        .then(data => {
            if (!data.points || data.points.length === 0) {
               if (currentPolyline) {
                  leafletMap.removeLayer(currentPolyline);
                  currentPolyline = null;
               }
               return;
            }
            const latlngs = data.points.map(p => [p.lat, p.lng]);
            if (currentPolyline) {
                leafletMap.removeLayer(currentPolyline);
            }
            currentPolyline = L.polyline(latlngs, { color: '#4f46e5', weight: 5 }).addTo(leafletMap);
            leafletMap.fitBounds(currentPolyline.getBounds(), { padding: [20, 20] });
        })
        .catch(err => {
            console.warn('GPX Fetch Error:', err);
            if (currentPolyline) {
                leafletMap.removeLayer(currentPolyline);
                currentPolyline = null;
            }
        });
}
</script>
"""
content = content.replace('{% block extra_js %}', '{% block extra_js %}\n' + inject_script)

content = content.replace('formProjects: [],', 'formProjects: [],\n    selectedRoadInfo: null,\n    selectRoad(road) {\n      this.selectedRoadInfo = road;\n      loadGPXData(road.id);\n    },')
content = content.replace("this._fetchProjects();", "this._fetchProjects();\n      setTimeout(initMap, 500);")

with open('templates/dashboard/roads/list.html', 'w') as f:
    f.write(content)
