import re

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

# add block extra_head or append to extra_css 
if '{% block extra_head %}' not in content:
    content = content.replace('{% block page_title %}Roads{% endblock %}', 
                              '{% block page_title %}Roads{% endblock %}\n' + css)


# replace layout
new_layout = """
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6 mt-4">
    
    <!-- Left panel: Filters & List -->
    <div class="lg:col-span-1 flex flex-col gap-4">
"""
content = content.replace('  <!-- Filters -->', new_layout + '  <!-- Filters -->')

end_of_left = """
    </div>

    <!-- Right panel: Map & Details -->
    <div class="lg:col-span-2 flex flex-col gap-4">
      <div class="card p-4">
          <h2 class="text-base font-semibold text-slate-800 mb-2">Road Map View</h2>
          <div id="map" class="w-full h-[500px] bg-slate-100 rounded-xl mb-4 border border-slate-200"></div>
          
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
                      <span class="font-medium text-slate-700"><span x-text="selectedRoadInfo?.length || '-'"></span> km</span>
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

content = content.replace('    <!-- Pagination -->', '    <!-- Pagination -->')
# We need to wrap the whole left section properly
# we can inject end_of_left right before <!-- Create/Edit Modal -->

content = content.replace('  <!-- Create/Edit Modal -->', end_of_left + '\n  <!-- Create/Edit Modal -->')


# Change the table rows to make them clickable
table_row_old = '<tr class="hover:bg-slate-50 transition-colors">'
table_row_new = '<tr class="hover:bg-slate-50 transition-colors cursor-pointer" @click="selectRoad(road)" :class="selectedRoadInfo?.id === road.id ? \'bg-indigo-50/50\' : \'\'">'
content = content.replace(table_row_old, table_row_new)

# Stop event propagation for action buttons so they don't trigger selectRoad
actions_old = '<div class="flex items-center justify-end gap-1.5">'
actions_new = '<div class="flex items-center justify-end gap-1.5" @click.stop>'
content = content.replace(actions_old, actions_new)


# inject script
inject_script = """
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
let leafletMap = null;
let currentPolyline = null;

function initMap() {
    if (!leafletMap) {
        leafletMap = L.map('map').setView([28.6, 77.2], 10);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19
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
            if (!data.points || data.points.length === 0) return;
            const latlngs = data.points.map(p => [p.lat, p.lng]);
            if (currentPolyline) {
                leafletMap.removeLayer(currentPolyline);
            }
            currentPolyline = L.polyline(latlngs, { color: '#4f46e5', weight: 4 }).addTo(leafletMap);
            leafletMap.fitBounds(currentPolyline.getBounds(), { padding: [20, 20] });
        })
        .catch(err => {
            console.warn(err);
            if (currentPolyline) leafletMap.removeLayer(currentPolyline);
        });
}
</script>
"""

content = content.replace('{% block extra_js %}', '{% block extra_js %}\n' + inject_script)

# inject state in objects
# finding `formProjects: [],`
content = content.replace('formProjects: [],', 'formProjects: [],\n    selectedRoadInfo: null,\n    selectRoad(road) {\n      this.selectedRoadInfo = road;\n      loadGPXData(road.id);\n    },')

with open('templates/dashboard/roads/list.html', 'w') as f:
    f.write(content)
