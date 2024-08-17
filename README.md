# Smol XML

A very small library for parsing XML files with a focus on an intuitive and easy-to-use API.

This is barely tested, doesn't check whether the provided XML document is valid and has no proper error reporting. Mainly useful for prototyping and short scripts that just want to extract some of the elements with ease.

## How to use

For a simple example, see also [test.py](./test.py).

0. Import the library into your script

```py
import smolXML as xml
```

1. Parse your XML text to receive the root element of your XML document

```py
# If you want to read in a file, provide the path to the file here:
root = xml.parseFile("my-file.xml")

# If you want to just parse a string, use the following function instead
root = xml.parseStr("<p>This is an XML document</p>")
```

Note: If your XML document contains several top-level elements, an AssertionError will be thrown.

2. Simply query the elements you want

```py
# There are many ways to get the elements you want
# The following shows how to use the different available functions

# You can get the first child of a specific type with any of the following ways
first_child = root["container"]
first_child = root.getFirstChildByName("container")

# When you want all children with the type/name "container":
containers = root.getAllChildrenByName("container")

# You can get the first child of a specific path with any of the following ways
# It is assumed that "root" contains the document shown in the example below here
first_organization = root["count"]["akn4un:voters"]["organization"]
first_organization = root.getFirstChildByPath("count", "akn4un:voters", "organization")
# Per the example, "first_organization" would now contain ECUADOR as a child

# You can also get all children of a specific path:
all_organizations = root.getAllChildrenByPath("count", "akn4un:voters", "organization")
# Per the example, "all_organizations" would now be a list containing all of the "organization" elements shown below

# When you want to get the string contents of an element, you have the following options:
# 1. If you know there's only one child and it's a string (like with the "organization" example)
name_of_organization = first_organization.children[0]
name_of_organization == "ECUADOR"
# 2. If there might be several children, but you want to get only the text contained within there
# As an example, take the Element "<p> <span>Reference</span> to this bla bla</p>"
only_the_string = element.getStrVal()
only_the_string == "Reference to this bla bla"
```

1. Enjoy the extra lifetime you gained by using this XML parser over the over-engineered alternatives

## Element

The following shows the structure of the `xml.Element` type.

To simplify explanation, assume our element looks as follows in XML:

```xml
<voting source="#un" name="resolution">
	<count value="011" refersTo="inFavour">
		<akn4un:voters>
			<organization refersTo="memberState">ECUADOR</organization>
			<organization refersTo="memberState">FRANCE</organization>
			<organization refersTo="memberState">GUYANA</organization>
			<organization refersTo="memberState">JAPAN</organization>
			<organization refersTo="memberState">MALTA</organization>
			<organization refersTo="memberState">REPUBLIC OF KOREA</organization>
			<organization refersTo="memberState">SIERRA LEONE</organization>
			<organization refersTo="memberState">SLOVENIA</organization>
			<organization refersTo="memberState">SWITZERLAND</organization>
			<organization refersTo="memberState">UNITED KINGDOM</organization>
			<organization refersTo="memberState">UNITED STATES</organization>
		</akn4un:voters>
	</count>
	<count value="004" refersTo="abstaining">
		<akn4un:voters>
			<organization refersTo="memberState">ALGERIA</organization>
			<organization refersTo="memberState">CHINA</organization>
			<organization refersTo="memberState">MOZAMBIQUE</organization>
			<organization refersTo="memberState">RUSSIAN FEDERATION</organization>
		</akn4un:voters>
	</count>
</voting>
```

An element has the following properties:

- `type`: This is the name of the element. In the above example, the type would be `voting`
- `attrs`: This a dictionary mapping the keys of the element's attributes to its values. In the example, this would be `{ source: "#un", name: "resolution" }`
- `children`: This is a list containing all child elements. In the example, there would be two children, each with `type == count`. A child can also be a string. For example, all of the elements with `type == organization` have only one child of type string.

If you ever want to see the structure of an Element, you can print the element and it will show you all of these properties. (Be warned that it will also print all children and their children and so on, so it might produce a lot of output potentially).

If you want to see how the element would look as XML again, you can call `print(my_element.toXML())`.
