import xml.etree.ElementTree

class boardEdge():
    def __init__(self, pos_from, transportation, pos_to):
        self.pos_from = pos_from
        self.transportation = transportation
        self.pos_to = pos_to

    def get_pos_from(self):
        return self.pos_from

    def get_transportation(self):
        return self.transportation

    def get_pos_to(self):
        return self.pos_to

    def __hash__(self):
        return hash((self.pos_from, self.transportation, self.pos_to))

    def __eq__(self, other):
        return other and self.pos_from == other.pos_from and self.transportation == other.transportation and self.pos_to == other.pos_to


root = xml.etree.ElementTree.parse('board_file.xml').getroot()

boardEdges = set()
for child in root:
    for action in child:
        trans = action.find('transportation').text
        src = min(child.attrib['id'], action.find('destination').text)
        dest = max(child.attrib['id'], action.find('destination').text)
        e = boardEdge(src, trans, dest)
        boardEdges.add(e)

file = open("trueLayout.txt","w")
file.write("200\n")

for i in boardEdges:
    file.write(i.get_transportation().upper() + "; " + i.get_pos_from() + " : : " + i.get_pos_to() + "\n")