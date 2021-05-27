import networkx as nx
import pandas as pd
import plotly.graph_objects as go


def make_temporal_plot():
    """
    Make the network and slider
    """
    edges = pd.read_csv('data/temporal_edges_sampled.csv')
    edge_traces = []
    node_traces = []
    years = ['2017', '2018', '2019', '2020']
    for year in years:
        filtered_edges = edges[edges['year'] == int(year)]
        G = nx.from_pandas_edgelist(filtered_edges, edge_attr=True)
        # Trim the graph
        remove = [node for node,degree in dict(G.degree()).items() if degree < 20]
        G.remove_nodes_from(remove)
        pos = nx.spring_layout(G)
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0 = pos[edge[0]][0]
            y0 = pos[edge[0]][1]
            x1 = pos[edge[1]][0]
            y1 = pos[edge[1]][1]
            #x0, y0 = G.nodes[edge[0]]['pos']
            #x1, y1 = G.nodes[edge[1]]['pos']
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        edge_trace = go.Scatter(
            visible=False,
            name="year",
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        for p in pos:
            x = pos[p][0]
            y = pos[p][1]
            #x, y = G.nodes[node]['pos']
            node_x.append(x)
            node_y.append(y)

        node_trace = go.Scatter(
            visible=False,
            name="year",
            x=node_x, y=node_y,
            mode='text+markers',
            hoverinfo='text',
            text = [n for n in G.nodes()],
            marker=dict(
                showscale=True,
                # colorscale options
                #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
                #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
                #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
                colorscale='YlGnBu',
                reversescale=True,
                color=[],
                size=10,
                colorbar=dict(
                    thickness=15,
                    title='Node Connections',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2))


        # add color
        node_adjacencies = []
        node_text = []
        for node, adjacencies in enumerate(G.adjacency()):
            node_adjacencies.append(len(adjacencies[1]))
            node_text.append('# of connections: '+str(len(adjacencies[1])))

        node_trace.marker.color = node_adjacencies
        # Can add number of connections when scroll over nodes
        node_trace.hovertext = node_text

        #fig.add_trace(edge_trace)
        #fig.add_trace(node_trace)
        edge_traces.append(edge_trace)
        node_traces.append(node_trace)

    fig = go.Figure(data=edge_traces + node_traces, layout=go.Layout(
                title='Temporal 13F-HR Investment Network',
                width=1000,
                height=750,
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

    # Make 2015 trace visible
    fig.data[0].visible = True
    fig.data[6].visible = True
    num_steps = int(len(fig.data) / 2)
    # Create and add slider
    steps = []
    for i in range(num_steps):
        step = dict(
            method="update",
            args=[{"visible": [False] * len(fig.data)},
                  {"title": "Slider switched to year: " + years[i]}],  # layout attribute
                    label=years[i]
        )
        step["args"][0]["visible"][i] = True  # Toggle i'th trace to "visible"
        step["args"][0]["visible"][i + num_steps] = True
        steps.append(step)

    sliders = [dict(
        active=10,
        currentvalue={"prefix": "Year: "},
        pad={"t": 50},
        steps=steps
    )]

    fig.update_layout(
        sliders=sliders
    )


    return fig
