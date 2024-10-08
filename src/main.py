from xml.dom.minidom import parse 				# Parses .osm doc
from graph_elements.graph import Graph 			# Graph object
from parsing import filter_ways, filter_nodes	# Extra post processing on .osm
from graph_elements.utils import *				# Extra post processing on .osm 
from visualization import *          			# Visualize the graph
from time import time							# Benchmarking
from math import floor							# Benchmarking
import csv

if __name__=="__main__":

	file_location = input(".osm file location: ")
	
	start = time()	
	# Move the xml file into DOM
	dom = None
	try:
		dom = parse(file_location)
	except:
		raise Exception("No such file")

	name = file_location.split("/")[-1].split(".")[0]
	print("file name: {}".format(name))
 
	stop = time()
	print("Parsed .osm in {} milliseconds".format(floor((stop - start)*1000.0)))

	# Gather all of the nodes and ways in the file
	way_elems = list(dom.getElementsByTagName("way"))
	node_elems = list(dom.getElementsByTagName("node"))

	# Filter the ways and nodes to the ones we care about
	# way_elems  = filter_ways(way_elems)
	# node_elems = filter_nodes(node_elems, way_elems)

	# Create the graph
	g = Graph()

	start = time()	
	# Now that we have the data in a convenient form, parse it into the graph
	for elem in node_elems:
		g.add_node(elem)

	stop = time()
	print("Added {} nodes in {} milliseconds".format(len(g.nodes), floor((stop - start)*1000.0)))

	print("Do you have a polygon to clean the data? (highly recommended)")
	bool_have_ploygon = input("[y/n]: ")

	if bool_have_ploygon == "y":
		
		polygon_file_location = input("Polygon file location: ")

		# Remove the node if it's not in the polygon of selinsgrove
		try:
			point_in_polygon(g, polygon_file_location)
		except:
			raise Exception("No such file")

	start = time()
	# Adding ways is a lot more complicated
	# For each way,
	for elem in way_elems:
   
    # debug print
		print("Way ID: {}".format(elem.getAttribute("id")))
		
		# Get the nd_tags
		nd_tags = list(elem.getElementsByTagName("nd"))
		
		# Get the IDs off of those tags
		node_ids = list(map(lambda x: int(x.getAttribute("ref")), nd_tags))
		node_ids = list(filter(lambda x: x in [y.iden for y in g.nodes], node_ids))
		
		# Collect the nodes in our graph
		# structure that pertain to this way
		nodes = []
		for i in range(len(g.nodes)):
			if g.nodes[i].iden in node_ids:
				nodes.append(g.nodes[i])

		# Run the minimum spanning tree algo to
		# figure out how they ought to be linked up
		connections = kruskal(nodes)

		# Add those edges
		for n1,n2 in connections:
			g.add_edge(n1, n2)

	stop = time()
	print("Added {} ways in {} milliseconds".format(len(g.edges), floor((stop - start)*1000.0)))

	print("Length of all edges: {} kilometers".format(int(g.get_length())/1000))

	# Needed modification to the graph to compute the shortest route
	start = time()
	make_graph_eulerian(g)
	stop = time()
	print("Made graph eulerian in {} milliseconds".format(floor((stop - start)*1000.0)))

	# Length of graph after modification
	print("Length of all edges (after modification): {} kilometers".format(int(g.get_length())/1000))

	# Generate Eulerian path
	starting_node = g.nodes[0]
	path = hierholzer(g.to_node_dictionary(), starting_node)
 
 	# Define the fieldnames
	fieldnames = ['id', 'lat', 'lng', 'x', 'y', 'index']

	# save path to .txt file
 

	with open("data/{}.csv".format(name), "w") as file:
		# Create a writer object
		writer = csv.DictWriter(file, fieldnames=fieldnames)
		writer.writeheader()
		for i, node in enumerate(path):
			writer.writerow({'id': node.iden, 'lat': node.lat_lon[0], 'lng': node.lat_lon[1], 'x': node.x, 'y': node.y, 'index': i})

	print("Done. How do you want to view the data?")
	print("1. Show map")
	print("2. Show heatmap (edges we need to cross multiple times)")
	print("3. Show route animation")

	option = input("input [1/2/3]: ")

	if option == "1":
		display_graph(g)	
	elif option == "2":
		print("This takes a moment...")
		display_graph(g, heatmap=True)	
	elif option == "3":
		# Optionally, you can set a speed of animation. Where "speed" is how long we display one frame of the animation
		# bigger number -> slower
		speed = 10
		animate_walk(path, speed)	
	else:
		raise Exception("Not a valid option")