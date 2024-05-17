# Import packages
from dash import Dash, html, dcc, Output, Input, State, callback
import pandas as pd

from collector_sed.sed_model import CollectorParams, SedCell, CollectionSection


def draw_fig(
    cut_depth: float = 0.1,
    left_right_ratio: float = 0.5,
    sed_settled_density: float = 120.0,
    sed_base_density: float = 350.0,
    sed_percent_to_settle: float = 0.3,
    number_of_cells: int = 50,
    stop: int = None,
):
    cp = CollectorParams(cut_depth)
    sc = SedCell(
        left_right_ratio,
        sed_settled_density,
        sed_base_density,
        sed_percent_to_settle,
    )
    cs = CollectionSection(sc, number_of_cells, cp)

    cs.run_model(stop)
    return cs.get_plotly_graph(continuous_colours=True)


# Incorporate data
df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv"
)

# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(
        [
            html.Div(
                children=[
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
                    html.Label("Number of cells"),
                    dcc.Slider(
                        step=1,
                        min=5,
                        max=50,
                        value=50,
                        marks=None,
                        id="cells-slider",
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Label("Stop on cell"),
                    dcc.Slider(
                        step=1,
                        min=1,
                        max=50,
                        value=50,
                        marks=None,
                        id="stop-slider",
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Button("Run", id="run-button", n_clicks=0),
                ],
                style={"padding": 10, "flex": 1},
            ),
            html.Div(
                children=[dcc.Graph(figure=draw_fig(), id="graph")],
                style={"padding": 10, "flex": 3},
            ),
        ],
        style={"display": "flex", "flexDirection": "row"},
    ),
    html.Div(
        [html.P("")],
    ),
]


@callback(
    Output("graph", "figure"),
    Input("run-button", "n_clicks"),
    State("graph", "figure"),
    State("cut-depth-slider", "value"),
    State("left-right-slider", "value"),
    State("percent-sttle-slider", "value"),
    State("settled-density-slider", "value"),
    State("base-density-slider", "value"),
    State("cells-slider", "value"),
    State("stop-slider", "value"),
    prevent_initial_call=True,
)
def run_model(
    _,
    old_fig,
    cut_depth,
    left_right,
    percent_settle,
    settled_density,
    base_density,
    cells,
    stop,
):
    fig = draw_fig(
        cut_depth=cut_depth,
        left_right_ratio=left_right,
        sed_percent_to_settle=percent_settle,
        sed_settled_density=settled_density,
        sed_base_density=base_density,
        number_of_cells=cells,
        stop=stop,
    )

    fig["layout"] = old_fig["layout"]
    return fig


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
