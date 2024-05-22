# Import packages
import json
from dash import Dash, html, dcc, Output, Input, State, callback, ctx
import dash_bootstrap_components as dbc
import pandas as pd

from collector_sed.sed_model import CollectorParams, SedCell, CollectionSection

MAX_CELLS = 50
CUT_DEPTH = 0.1
PROPORTION_UP_RISER = 0.0
EXTRA_SETTLED_CUT_DEPTH = 0.0
LEFT_RIGHT_RATIO = 0.5
SETTLED_DENSITY = 120.0
BASE_DENSITY = 350.0
PERCENT_TO_SETTLE = 0.1
NUMBER_OF_CELLS = 50
START_CELL = 20
END_CELL = 30
COLORBY = "name"
EXTRA_CELLS = []

HELP_TEXT = """This app roughly simulates the action of the collector vehicle traversing the seafloor and redistributing sediment laterally along the seafloor. The view is a cross section of the seafloor with the collector vehicle moving into and out of the screen. Each "cell" is one collector track.

Change the settings and set the `Start` and `Stop` cells, then click `Run`. The seafloor can also be clicked to pass the collector through that cell after the cells defined by `Start` and `Stop`.

Settings:

* Cut Depth - the depth that the collector vehicle cuts into the seafloor.

* Extra cut depth -  An "extra" amount of cut can be set to take up more of the deposited sediment.

* Left to right ratio - How much of the sediment goes left, and how much goes right. 1: all the sediment goes left, 0: all the sediment goes right.

* Percent to settle - Proportion of the sediment that settles on each cell.

* Settled density - the dry bulk density of the settled sediment.

* Base density - the dry bulk density of the original seafloor.

* Number of cells - effectively the width of the simulation.

* Start and Stop cells - the simulation can be set to automatically run from cell Start to cell Stop, left to right.

* Color by horizon - Each cell is colored by horizon, so all cells from the same settling event or collector pass have the same color.

* Color by distance travelled - Each cell is covered by the distance that sediment travelled from the collector track where it originated.

* Run - Run the simulation with the given Settings.

* Reset clicked cells - Reset any cells that have been clicked."""


def draw_fig(
    cut_depth: float = CUT_DEPTH,
    extra_settled_cut_depth: float = EXTRA_SETTLED_CUT_DEPTH,
    proportion_up_riser: float = PROPORTION_UP_RISER,
    left_right_ratio: float = LEFT_RIGHT_RATIO,
    sed_settled_density: float = SETTLED_DENSITY,
    sed_base_density: float = BASE_DENSITY,
    sed_percent_to_settle: float = PERCENT_TO_SETTLE,
    number_of_cells: int = NUMBER_OF_CELLS,
    start: int = START_CELL,
    stop: int = END_CELL,
    colorby: str = COLORBY,
    extra_cells: list[int] = EXTRA_CELLS,
):
    cp = CollectorParams(cut_depth, proportion_up_riser, extra_settled_cut_depth)
    sc = SedCell(
        left_right_ratio,
        sed_settled_density,
        sed_base_density,
        sed_percent_to_settle,
    )
    cs = CollectionSection(sc, number_of_cells, cp)

    cs.run_model(start, stop, extra_cells=extra_cells)
    return cs.get_plotly_graph(color_by=colorby)


# Initialize the app
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

help_modal_button = dbc.Button("Help...", id="open", n_clicks=0, color="link")

help_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Help")),
        dbc.ModalBody(dcc.Markdown(HELP_TEXT)),
        dbc.ModalFooter(
            dbc.Button("Close", id="close", className="ms-auto", n_clicks=0)
        ),
    ],
    id="modal",
    is_open=False,
    size="xl",
)

controls = [
    dbc.Col(
        [
            html.Label("Cut depth (m)"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=0.5,
                value=CUT_DEPTH,
                id="cut-depth-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Extra cut depth for settled sediment (m)"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=0.5,
                value=EXTRA_SETTLED_CUT_DEPTH,
                id="cut-depth-extra-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Left to right ratio"),
            dcc.Slider(
                step=0.1,
                min=0,
                max=1,
                value=LEFT_RIGHT_RATIO,
                id="left-right-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Percent to settle"),
            dcc.Slider(
                step=0.01,
                min=0,
                max=1,
                value=PERCENT_TO_SETTLE,
                id="percent-sttle-slider",
                marks=None,
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Settled density"),
            dcc.Slider(
                step=1,
                min=100,
                max=400,
                value=SETTLED_DENSITY,
                marks=None,
                id="settled-density-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Base density"),
            dcc.Slider(
                step=1,
                min=100,
                max=500,
                value=BASE_DENSITY,
                marks=None,
                id="base-density-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
        ]
    ),
    dbc.Col(
        [   
            html.Label("Proportion of sediment up riser"),
            dcc.Slider(
                step=0.01,
                min=0.0,
                max=1.0,
                value=PROPORTION_UP_RISER,
                marks=None,
                id="riser-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Number of cells"),
            dcc.Slider(
                step=1,
                min=5,
                max=MAX_CELLS,
                value=MAX_CELLS,
                marks=None,
                id="cells-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Start on cell"),
            dcc.Slider(
                step=1,
                min=0,
                max=MAX_CELLS,
                value=START_CELL,
                marks=None,
                id="start-slider",
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            html.Label("Stop on cell"),
            dcc.Slider(
                step=1,
                min=0,
                max=MAX_CELLS,
                value=END_CELL,
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
                value=COLORBY,
                inline=True,
                id="colorby-radio",
            ),
            dbc.Button(
                "Run", color="success", id="run-button", n_clicks=0, className="m-3"
            ),
            dbc.Button(
                "Reset clicked cells",
                id="reset-extra",
                color="warning",
                n_clicks=0,
                className="me-1",
            ),
            help_modal_button,
            help_modal,
            dcc.Store(id="data-store", storage_type="session"),
        ]
    ),
]

graph = dbc.Col([html.Div(dcc.Graph(figure=draw_fig(), id="graph"))])

app.layout = [dbc.Container([dbc.Row(controls), dbc.Row(graph)], fluid=True)]


@callback(
    Output("data-store", "data"),
    Output("graph", "figure", allow_duplicate=True),
    Input("run-button", "n_clicks"),
    Input("reset-extra", "n_clicks"),
    Input("graph", "clickData"),
    State("data-store", "data"),
    State("graph", "figure"),
    State("cut-depth-slider", "value"),
    State("cut-depth-extra-slider", "value"),
    State("left-right-slider", "value"),
    State("percent-sttle-slider", "value"),
    State("settled-density-slider", "value"),
    State("base-density-slider", "value"),
    State("riser-slider", "value"),
    State("cells-slider", "value"),
    State("start-slider", "value"),
    State("stop-slider", "value"),
    State("colorby-radio", "value"),
    prevent_initial_call=True,
)
def make_graph(
    _,
    __,
    graph_click_data,
    datastore,
    old_fig,
    cut_depth,
    cut_depth_extra,
    left_right_ratio,
    sed_percent_settle,
    sed_settled_density,
    sed_base_density,
    proportion_up_riser,
    number_of_cells,
    start,
    stop,
    colorby,
):
    if datastore is not None:
        labels = json.loads(datastore)
    else:
        labels = []

    if ctx.triggered_id == "graph" and graph_click_data is not None:
        labels.append(graph_click_data["points"][0]["label"])
        # labels = list(set(labels))

    if ctx.triggered_id == "reset-extra":
        labels = []

    fig = draw_fig(
        cut_depth=cut_depth,
        extra_settled_cut_depth=cut_depth_extra,
        proportion_up_riser=proportion_up_riser,
        left_right_ratio=left_right_ratio,
        sed_percent_to_settle=sed_percent_settle,
        sed_settled_density=sed_settled_density,
        sed_base_density=sed_base_density,
        number_of_cells=number_of_cells,
        start=start,
        stop=stop,
        colorby=colorby,
        extra_cells=labels,
    )

    fig["layout"] = old_fig["layout"]

    return json.dumps(labels), fig


@app.callback(
    Output("modal", "is_open"),
    [Input("open", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
