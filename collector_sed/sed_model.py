import copy
from dataclasses import dataclass, field
from typing import List, Literal, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BED_BOTTOM = -0.2

def cut_settled_only(
    bed_layers: pd.DataFrame, cut_depth: float
) -> Tuple[pd.DataFrame, float]:
    settled_layers = bed_layers[bed_layers["type"] == "settled"]
    bed = bed_layers[bed_layers["type"] == "bed"]

    if settled_layers.empty:
        return bed_layers, 0.0

    absolute_cut = settled_layers["top"].max() - cut_depth
    df_partial_cut = settled_layers[settled_layers["bottom"] < absolute_cut]
    df_partial_cut.reset_index(inplace=True, drop=True)
    if not df_partial_cut.empty:
        df_partial_cut.loc[0, "top"] = absolute_cut

    final_bedlayers = pd.concat([df_partial_cut, bed], ignore_index=True)

    settled_cut = abs(bed_layers["top"].values[0] - final_bedlayers["top"].values[0])

    return final_bedlayers, settled_cut


def cut_sedbed(
    bed_layers: pd.DataFrame, cut_depth: float, cut_extra_settled: float = None
) -> Tuple[pd.DataFrame, float, float]:
    if cut_extra_settled is not None:
        precut_bed_layers, cut_settled = cut_settled_only(bed_layers, cut_extra_settled)
    else:
        cut_settled = 0.0
        precut_bed_layers = bed_layers

    # Cut into the bed dataframe
    absolute_cut = precut_bed_layers["top"].max() - cut_depth

    # df_cut_complete = self.bed_layers[self.bed_layers['bottom'] >= absolute_cut]
    df_partial_cut = precut_bed_layers[precut_bed_layers["bottom"] < absolute_cut]
    df_partial_cut.reset_index(inplace=True, drop=True)
    df_partial_cut.loc[0, "top"] = absolute_cut
    new_bed_layers = df_partial_cut

    # compare = bed_layers.compare(new_bed_layers)

    cut_bed = abs(new_bed_layers["top"].values[-1] - bed_layers["top"].values[-1])
    cut_settled += cut_depth - cut_bed

    return new_bed_layers, cut_bed, cut_settled


@dataclass
class SedimentBed:
    bed_top: float = 0.0
    bed_bottom: float = BED_BOTTOM
    settled_top: float = 0.0
    bed_layers: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        self.bed_layers = pd.DataFrame(
            {
                "top": [self.bed_top],
                "bottom": [self.bed_bottom],
                "type": ["bed"],
                "name": ["existing"],
                "origin_cell": [None],
            }
        )

    def cut(
        self, cut_depth: float, cut_extra_settled: float = None
    ) -> Tuple[float, float]:
        new_bed_layers, cut_bed, cut_settled = cut_sedbed(
            self.bed_layers, cut_depth, cut_extra_settled
        )
        self.bed_layers = new_bed_layers

        return cut_bed, cut_settled

    def settle(self, settle_thickness, name: str, origin_cell: int):
        self.settled_top += settle_thickness

        current_top = self.bed_layers["top"].max()
        new_top = current_top + settle_thickness

        new_layer = pd.DataFrame(
            {
                "top": [new_top],
                "bottom": [current_top],
                "type": ["settled"],
                "name": [name],
                "origin_cell": [origin_cell],
            }
        )
        self.bed_layers = pd.concat([new_layer, self.bed_layers], ignore_index=True)


@dataclass
class CollectorParams:
    # collector_width: float
    cut_depth: float
    proportion_up_riser: float
    extra_settled_cut_depth: float = None


@dataclass
class SedCell:
    # variable
    left_right_ratio: float
    sed_settled_density: float
    sed_base_density: float
    # nodule_percentage_by_volume: float
    sed_percent_to_settle: float

    # incoming
    # incoming_mass: float = None

    # outgoing
    sed_to_pass_left: float = 0.0
    sed_to_pass_right: float = 0.0

    # state
    sediment_bed: SedimentBed = field(default_factory=SedimentBed)

    def apply_collector(self, cv: CollectorParams, pass_name: str, origin_cell: int):
        mass_collected_pre_riser = self._get_sediment_mass(cv)

        # Take away proportion for the riser
        mass_collected = mass_collected_pre_riser * (1 - cv.proportion_up_riser)
        
        # Don't forget to settle some ON this cell
        mass_to_settle = mass_collected * self.sed_percent_to_settle
        self._settle(mass_to_settle, pass_name, origin_cell)

        mass_to_pass = mass_collected - mass_to_settle
        self.sed_to_pass_left = mass_to_pass * self.left_right_ratio
        self.sed_to_pass_right = mass_to_pass - self.sed_to_pass_left

    def add_sediment(
        self, incoming_mass: float, direction: str, pass_name: str, origin_cell: int
    ):
        mass_to_settle = incoming_mass * self.sed_percent_to_settle
        self._settle(mass_to_settle, pass_name, origin_cell)

        if direction == "left":
            self.sed_to_pass_left = incoming_mass - mass_to_settle
        elif direction == "right":
            self.sed_to_pass_right = incoming_mass - mass_to_settle
        else:
            raise ValueError(f"Unknown direction: {direction}")

    def _settle(self, mass: float, name: str, origin_cell: int):
        settled_thickness = mass / self.sed_settled_density
        self.sediment_bed.settle(settled_thickness, name, origin_cell)

    def _get_sediment_mass(self, cv: CollectorParams):
        # Get sediment mass taken by collector

        # First get from the settled

        cut_bed, cut_settled = self.sediment_bed.cut(
            cv.cut_depth, cv.extra_settled_cut_depth
        )

        total_mass = (cut_settled * self.sed_settled_density) + (
            cut_bed * self.sed_base_density
        )

        return total_mass


@dataclass
class CollectionSection:
    seed_cell: SedCell
    number_of_cells: int
    collector: CollectorParams
    cells: List[SedCell] = field(default_factory=list)
    mass_lower_limit: float = 0.01

    def __post_init__(self):
        self.cells = []
        for _ in range(self.number_of_cells):
            self.cells.append(copy.deepcopy(self.seed_cell))

    def run_model(
        self, start: int = None, stop: int = None, extra_cells: list[int] = []
    ):
        # Iterate over cells from right to left appling the
        # Collector vehicle

        if start is None:
            start = 0

        if stop is None:
            stop = self.number_of_cells

        if start > stop:
            return

        label = 0

        for i in range(start, stop):
            if stop is not None and i == stop:
                break

            self._run_on_cell(i, str(label))
            label += 1

        for i in extra_cells:
            self._run_on_cell(i, label)
            label += 1

    def _run_on_cell(self, i: int, label: str):
        c = self.cells[i]

        c.apply_collector(self.collector, label, i)
        self._iterate_cells(label, i)

    def get_tops(self) -> Tuple[list, list]:
        # Get a list of settled tops and bed tops
        settled_tops = [c.sediment_bed.settled_top for c in self.cells]
        bed_tops = [c.sediment_bed.bed_top for c in self.cells]
        return settled_tops, bed_tops

    def get_sections(self) -> pd.DataFrame:
        df_all = pd.DataFrame()
        for i, cell in enumerate(self.cells):
            df = cell.sediment_bed.bed_layers
            df["cell_number"] = i

            df_all = pd.concat([df_all, df], ignore_index=True)

        df_all["thickness"] = abs(df_all["bottom"] - df_all["top"])
        df_all['thickness2'] = df_all['thickness'] # hack because of the way px aggregates data, the original thickness is lost
        total_thicknesses = df_all[df_all['type'] == 'settled'].groupby('cell_number').sum(numeric_only=True)['thickness2']
        total_thicknesses = abs(total_thicknesses)
        total_thicknesses.rename('total_thickness', inplace=True)
        df_all = pd.merge(df_all, total_thicknesses, on='cell_number')

        df_all["origin_cell"] = pd.to_numeric(df_all["origin_cell"], errors="coerce")
        df_all["proximity"] = abs(df_all["origin_cell"] - df_all["cell_number"])
        
        
        
        return df_all

    def get_plotly_graph(self, color_by: Literal["name", "proximity"]) -> go.Figure:
        df = self.get_sections()

        if not color_by in ["name", "proximity"]:
            raise ValueError("Unknown color by variable")

        if color_by == "name":
            df["name"] = pd.to_numeric(df["name"], errors="coerce")

        fig = px.bar(
            df,
            x="cell_number",
            y="thickness",
            base="bottom",
            color=color_by,
            hover_name='cell_number',
            hover_data={
                'top': True,
                'bottom': True,
                'thickness': True, # For some reason thickness is displaying the wrong value (top)
                'cell_number': True,
                'name': True,
                'thickness2': True,
                'total_thickness': True
            },
        )
        fig.update_layout(
            bargap=0.0,
            coloraxis_colorbar=dict(
                title=color_by,
            ),
        )
        fig.update_traces(hovertemplate="<b>Cell: %{hovertext}</b><br><br>Name=%{customdata[1]:.3f}<br>Top=%{y:.3f}<br>Bottom=%{base:.3f}<br>Thickness: %{customdata[2]:.3f}<br>Total thickness: %{customdata[3]:.3f}<br><extra></extra>")

        fig.data[0].marker.line.width = 0

        return fig

    def _iterate_cells(self, pass_name: str, origin_cell: int):
        # Pass over the cells until all the sediment has
        # settled or passed out of scope

        passed_sediment = True
        while passed_sediment:
            passed_sediment = False
            for i in range(self.number_of_cells):
                cell = self.cells[i]
                if cell.sed_to_pass_left > self.mass_lower_limit:
                    passed_sediment = True

                    if i != 0:
                        self.cells[i - 1].add_sediment(
                            cell.sed_to_pass_left, "left", pass_name, origin_cell
                        )

                    cell.sed_to_pass_left = 0.0

                if cell.sed_to_pass_right > self.mass_lower_limit:
                    passed_sediment = True

                    try:
                        self.cells[i + 1].add_sediment(
                            cell.sed_to_pass_right, "right", pass_name, origin_cell
                        )
                    except IndexError:
                        pass

                    cell.sed_to_pass_right = 0.0


if __name__ == "__main__":
    cp = CollectorParams(cut_depth=0.1, proportion_up_riser=0.0)
    sc = SedCell(
        left_right_ratio=0.5,
        sed_settled_density=120.0,
        sed_base_density=350.0,
        sed_percent_to_settle=0.3,
    )
    cs = CollectionSection(seed_cell=sc, number_of_cells=50, collector=cp)

    cs.run_model(stop=30)
    fig = cs.get_plotly_graph(continuous_colours=True)
    fig.write_html("first_figure.html", auto_open=True)
