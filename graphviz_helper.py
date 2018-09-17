def extract_path(paths, cpd, callback):
    for key,value in cpd.items():
        if isinstance(value, float):
            callback (paths + [key] + [value])
        else:
            extract_path(paths + [key], value, callback)


def render_table(variable, values, grids):

    span = len(values['cpd']) + 1
    prefix = '<<FONT POINT-SIZE="7"><TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"><TR><TD COLSPAN="' + str(span) +'">' + values['desc'] + '</TD></TR>'
    header = "<TR><TD></TD>"

    for ll, label in values['legend'].items():
        header = header + '<TD>'  + label + ' (' + variable.lower() + '_' + str(ll)  + ')</TD>'
    header = header + '</TR>'


    loop_row = len(grids)
    loop_col = len(grids[0])
    body = ""

    if loop_row > 1:
        for row in range(loop_row):
            body = body + "<TR>"
            for col in range(loop_col):
                body = body + "<TD>" + str(grids[row][col]) + "</TD>"
            body = body + "</TR>"

    else:
        body = "<TR><TD>" + str(variable).lower() + "</TD>"
        for col in range(loop_col-1):
            body = body + '<TD>' + str(grids[0][col+1]) + '</TD>'
        body = body + "</TR>"

    footer = '</TABLE></FONT>>'
    return prefix + header + body + footer

def render_grid(variable, values):

    paths = []
    def callback(array):
        if len(array):
            paths.append(array)

    extract_path([variable], values['cpd'], callback)

    loop_row = int(len(paths) / len(values['cpd'].keys()))
    loop_col = int(len(paths) / loop_row)
    grids = [[x*loop_col+y for x in range(loop_col+1)] for y in range(loop_row)]

    if loop_row > 1:
        for col in range(loop_col):
            for row in range(loop_row):
                labels = []
                x = col * loop_row + row
                for ll in range(2,len(paths[x])-1, 2):
                    labels.append('{}_{}'.format(paths[x][ll].lower(), str(paths[x][ll+1])))
                grids[row][0] = ', '.join(labels)
                grids[row][col+1] = paths[x][-1]
    else:
        grids[0][0] = str(variable).lower()
        for col in range(len(paths)):
            grids[0][col+1] = paths[col][-1]

    return grids

def render_graph(structures, variables):
    try:
        from graphviz import Digraph
    except:
        print("Python Dependency: pip install graphviz")
        print("Graphviz also needs to be installed on the host: brew install graphviz")

    g = Digraph('G')

    # print(structures)
    for pairs in structures:
        g.attr('node', shape='oval', color='gray')
        g.node(pairs[0], variables[pairs[0]]['desc'])
        g.node(pairs[1], variables[pairs[1]]['desc'])
        g.edge(pairs[0], pairs[1])

    return g

def render_graph_probabilities(g, variables):
    import random

    for var, values in variables.items():
        g.attr('node', shape = 'plaintext')
        grids = render_grid(var, values)

        table = render_table(var, values, grids)
        random.seed(hash(table))
        g.node('cpd_' + var, label=table, color='gray')
        if random.randint(0,1):
            g.edge( 'cpd_' + var, var, style='invis')
        else:
            g.edge( var, 'cpd_' + var, style='invis')

    return g

def render_values(variable, values):

    paths = []
    def callback(array):
        if len(array):
            paths.append(array)

    extract_path([variable], values['cpd'], callback)

    loop_row = int(len(paths) / len(values['cpd'].keys()))
    loop_col = int(len(paths) / loop_row)
    rotated_grids = [[y*loop_row+x for y in range(loop_row)] for x in range(loop_col)]

    if loop_row > 1:
        for col in range(loop_col):
            for row in range(loop_row):
                evidences = []
                x = col * loop_row + row
                for ll in range(2,len(paths[x])-1, 2):
                    evidences.append(paths[x][ll])
                rotated_grids[col][row] = paths[x][-1]
    else:
        for col in range(len(paths)):
            rotated_grids[0][row] = paths[col][-1]

    return evidences, rotated_grids

def build_BayesianModel(structures, variables):
    try:
        from pgmpy.models import BayesianModel
        from pgmpy.factors.discrete import TabularCPD
    except:
        print("Install pgmpy: pip install pgmpy")

    model = BayesianModel(structures)

    cpd = {}
    for v,vc in variables.items():
        keys = list(vc['cpd'].keys())

        if isinstance(vc['cpd'][keys[0]],dict):

            variable = v
            cardinality = len(list(vc['cpd'].values()))
            evidences, values = render_values(v,vc)
            evidence_cards = []
            for cc in evidences:
                evidence_cards.append(len(variables[cc]['cpd'].values()))
            cpd['cpd_'+str(variable).lower()] = TabularCPD(variable=v,
                                                           variable_card=cardinality,
                                                           values=values,
                                                           evidence=evidences,
                                                           evidence_card=evidence_cards)

        else:
            variable = v
            cardinality = len(list(vc['cpd'].values()))
            values = [list(vc['cpd'].values())]
            cpd['cpd_'+str(variable).lower()] = TabularCPD(variable=v, variable_card=cardinality, values=values)

    # Associating the CPDs with the network
    for cc in cpd.keys():
        print("adding {}".format(cc))
        model.add_cpds(cpd[cc])

    return model
