# Import packages
from dash import Dash, html, dcc, Output, Input, State, callback
import dash_bootstrap_components as dbc
import pandas as pd

from collector_sed.sed_model import CollectorParams, SedCell, CollectionSection

MAX_CELLS = 50


def draw_fig(
    cut_depth: float = 0.1,
    extra_settled_cut_depth: float = 0.1,
    left_right_ratio: float = 0.5,
    sed_settled_density: float = 120.0,
    sed_base_density: float = 350.0,
    sed_percent_to_settle: float = 0.3,
    number_of_cells: int = 50,
    start: int = None,
    stop: int = None,
    colorby: str = "name",
):
    cp = CollectorParams(cut_depth, extra_settled_cut_depth)
    sc = SedCell(
        left_right_ratio,
        sed_settled_density,
        sed_base_density,
        sed_percent_to_settle,
    )
    cs = CollectionSection(sc, number_of_cells, cp)

    cs.run_model(start, stop)
    return cs.get_plotly_graph(color_by=colorby)


# Incorporate data
df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv"
)

# Initialize the app
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = [
    dbc.Col(
        [
            html.Label("Cut depth (m)"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=0.5,
                value=0.1,
                id="cut-depth-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Extra cut depth for settled sediment (m)"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=0.5,
                value=0.1,
                id="cut-depth-extra-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Left to right ratio"),
            dcc.Slider(
                step=0.1,
                min=0,
                max=1,
                value=0.5,
                id="left-right-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Percent to settle"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=1,
                value=0.3,
                id="percent-sttle-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Settled density"),
            dcc.Slider(
                step=1,
                min=100,
                max=400,
                value=150,
                marks=None,
                id="settled-density-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Base density"),
            dcc.Slider(
                step=1,
                min=100,
                max=500,
                value=350,
                marks=None,
                id="base-density-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
        ]
    ),
    dbc.Col(
        [
            html.Label("Number of cells"),
            dcc.Slider(
                step=1,
                min=5,
                max=MAX_CELLS,
                value=50,
                marks=None,
                id="cells-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Start on cell"),
            dcc.Slider(
                step=1,
                min=0,
                max=MAX_CELLS,
                value=1,
                marks=None,
                id="start-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Stop on cell"),
            dcc.Slider(
                step=1,
                min=1,
                max=MAX_CELLS,
                value=50,
                marks=None,
                id="stop-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Color by"),
            dbc.RadioItems(
                options=[
                    {"label": "Horizon", "value": "name"},
                    {"label": "Distance travelled", "value": "proximity"},
                ],
                value="name",
                inline=True,
                id="colorby-radio"
            ),
            dbc.Button("Run", color="success", id="run-button", n_clicks=0),
        ]
    ),
]


graph = dbc.Col([html.Div(dcc.Graph(figure=draw_fig(), id="graph"))])

app.layout = [dbc.Container([dbc.Row(controls), dbc.Row(graph)], fluid=True)]


@callback(
    Output("graph", "figure"),
    Input("run-button", "n_clicks"),
    State("graph", "figure"),
    State("cut-depth-slider", "value"),
    State("cut-depth-extra-slider", "value"),
    State("left-right-slider", "value"),
    State("percent-sttle-slider", "value"),
    State("settled-density-slider", "value"),
    State("base-density-slider", "value"),
    State("cells-slider", "value"),
    State("start-slider", "value"),
    State("stop-slider", "value"),
    State("colorby-radio", "value"),
    prevent_initial_call=True,
)
def run_model(
    _,
    old_fig,
    cut_depth,
    cut_depth_extra,
    left_right_ratio,
    sed_percent_settle,
    sed_settled_density,
    sed_base_density,
    number_of_cells,
    start,
    stop,
    colorby,
):
    fig = draw_fig(
        cut_depth=cut_depth,
        extra_settled_cut_depth=cut_depth_extra,
        left_right_ratio=left_right_ratio,
        sed_percent_to_settle=sed_percent_settle,
        sed_settled_density=sed_settled_density,
        sed_base_density=sed_base_density,
        number_of_cells=number_of_cells,
        start=start,
        stop=stop,
        colorby=colorby,
    )

    fig["layout"] = old_fig["layout"]
    return fig


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
