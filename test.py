import sys
import parse
import CFG

sys.argv = ['parse.py', 'sample.txt']
result = parse.test_parse()
graph = CFG.generate_graph(result)
print(graph)
