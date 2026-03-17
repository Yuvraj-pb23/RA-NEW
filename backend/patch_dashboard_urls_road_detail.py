with open('dashboard/urls.py', 'r') as f:
    content = f.read()

if 'RoadDetailView' not in content:
    content = content.replace('RoadListView,', 'RoadListView,\n    RoadDetailView,')
    
    # Add url path
    url_patt = 'path("roads/<uuid:road_id>/view/", RoadDetailView.as_view(), name="road_detail"),\n'
    content = content.replace('path("roads/",            RoadListView.as_view(),          name="roads"),', 'path("roads/",            RoadListView.as_view(),          name="roads"),\n    ' + url_patt)

with open('dashboard/urls.py', 'w') as f:
    f.write(content)

