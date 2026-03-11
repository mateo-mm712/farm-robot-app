import sys
sys.path.insert(0,'/mnt/managed_home/farm-ng-user-mateomm2004/farm-robot-app/src')
from soil_monitor import get_app

app = get_app()
print('init start')
app.initialize()
print('init end')
