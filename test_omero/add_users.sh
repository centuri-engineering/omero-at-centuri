#! /usr/bin/sh
source server/venv3/bin/activate
omero login -u root@localhost:4064 -w omero
omero group add Beatles
omero user add john John Lennon --group-name Beatles -P nhoj
omero user add paul Paul McCartney --group-name Beatles -P luap
omero user add george George Harisson --group-name Beatles -P egroeg

omero group add BikiniKill
omero user add kathleen Kathleen Hanna --group-name BikiniKill -P neelhtak
omero user add kathi Kathi Wilcox  --group-name BikiniKill -P ithak
omero user add tobi Tobi Vail --group-name BikiniKill -P ibot
omero user add erica Erica Dawn --group-name BikiniKill -P acire
