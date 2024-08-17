import smolXML as xml

root = xml.parseFile("test/big_test.xml")

preamble = root["statement"]["preamble"]
containers = preamble.getAllChildrenByName("container")
for container in containers:
	print("CONTAINER:", container)

