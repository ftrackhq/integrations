import os
import ftrack


location_name = 'studio_default'
project_location = '~/ftrack_projects/' # This location has to be changed


def register(registry, **kw):

	ftrack.ensureLocation(location_name)
	structure = ftrack.ClassicStructure()
	accessor = ftrack.DiskAccessor(prefix=os.path.expanduser(project_location))

	location = ftrack.Location(
		location_name,
		accessor=accessor,
		structure=structure,
		priority=1
	    )

	registry.add(location)
