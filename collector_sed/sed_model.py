import copy
from dataclasses import dataclass, field
from typing import List, Tuple

import pandas as pd
import plotly.express as px


@dataclass
class SedimentBed:
    bed_top: float = 0.0
    settled_top: float = 0.0
    bed_layers: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __post_init__(self):
        self.bed_layers = pd.DataFrame(
            {"top": [0.0], "bottom": [-9999], "type": ["bed"], "name": ["existing"]}
        )

    def cut(self, cut_depth: float) -> Tuple[float, float]:
        # Cut into the bed by x amount
        # returns thickness of bed cut, thickness of settled cut
        cut_settled = 0.0
        cut_bed = 0.0

        # Cut into the bed dataframe
        absolute_cut = self.settled_top - cut_depth

        # df_cut_complete = self.bed_layers[self.bed_layers['bottom'] >= absolute_cut]
        df_partial_cut = self.bed_layers[self.bed_layers["bottom"] < absolute_cut]
        df_partial_cut.reset_index(inplace=True, drop=True)
        df_partial_cut.loc[0, "top"] = absolute_cut
        self.bed_layers = df_partial_cut

        if self.bed_top == self.settled_top:
            # no settled sediment
            cut_bed = cut_depth

            self.bed_top -= cut_bed
            self.settled_top = self.bed_top
        else:
            settled_thickness = self.settled_top - self.bed_top

            if cut_depth <= settled_thickness:
                # Only the settled sediment is cut

                cut_settled = cut_depth
                self.settled_top -= cut_settled
            else:
                # All the settled sediment and some amount of the
                # bed is cut
                cut_settled = settled_thickness
                cut_bed = cut_depth - settled_thickness

                self.bed_top -= cut_bed
                self.settled_top = self.bed_top

        return cut_bed, cut_settled

    def settle(self, settle_thickness, name: str):
        self.settled_top += settle_thickness

        current_top = self.bed_layers["top"].max()
        new_top = current_top + settle_thickness

        new_layer = pd.DataFrame(
            {
                "top": [new_top],
                "bottom": [current_top],
                "type": ["settled"],
                "name": [name],
            }
        )
        self.bed_layers = pd.concat([new_layer, self.bed_layers], ignore_index=True)


@dataclass
class CollectorParams:
    collector_width: float
    cut_depth: float


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

    def apply_collector(self, cv: CollectorParams):
        mass_collected = self._get_sediment_mass(cv)

        self.sed_to_pass_left = mass_collected * self.left_right_ratio
        self.sed_to_pass_right = mass_collected = self.sed_to_pass_left

    def add_sediment(self, incoming_mass: float, direction: str, pass_name: str):
        mass_to_settle = incoming_mass * self.sed_percent_to_settle
        settled_thickness = mass_to_settle / self.sed_settled_density
        self.sediment_bed.settle(settled_thickness, pass_name)

        if direction == "left":
            self.sed_to_pass_left = incoming_mass - mass_to_settle
        elif direction == "right":
            self.sed_to_pass_right = incoming_mass - mass_to_settle
        else:
            raise ValueError(f"Unknown direction: {direction}")

    def _get_sediment_mass(self, cv: CollectorParams):
        # Get sediment mass taken by collector

        # First get from the settled

        cut_bed, cut_settled = self.sediment_bed.cut(cv.cut_depth)

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
    mass_lower_limit: float = 0.001

    def __post_init__(self):
        self.cells = []
        for _ in range(self.number_of_cells):
            self.cells.append(copy.deepcopy(self.seed_cell))

    def run_model(self):
        # Iterate over cells from right to left appling the
        # Collector vehicle

        for i, c in enumerate(self.cells):
            c.apply_collector(self.collector)
            self._iterate_cells(str(i))

    def get_tops(self) -> Tuple[list, list]:
        # Get a list of settled tops and bed tops
        settled_tops = [c.sediment_bed.settled_top for c in self.cells]
        bed_tops = [c.sediment_bed.bed_top for c in self.cells]
        return settled_tops, bed_tops

    def _iterate_cells(self, pass_name: str):
        # Pass over the cells until all the sediment has
        # settled or passed out of scope

        passed_sediment = True
        while passed_sediment:
            passed_sediment = False
            for i in range(self.number_of_cells):
                cell = self.cells[i]
                if cell.sed_to_pass_left > self.mass_lower_limit:
                    passed_sediment = True

                    try:
                        self.cells[i - 1].add_sediment(
                            cell.sed_to_pass_left, "left", pass_name
                        )
                    except IndexError:
                        pass

                    cell.sed_to_pass_left = 0.0

                if cell.sed_to_pass_right > self.mass_lower_limit:
                    passed_sediment = True

                    try:
                        self.cells[i + 1].add_sediment(
                            cell.sed_to_pass_right, "right", pass_name
                        )
                    except IndexError:
                        pass

                    cell.sed_to_pass_right = 0.0


if __name__ == "__main__":
    cp = CollectorParams(15, 0.1)
    sc = SedCell(0.5, 120.0, 350.0, 0.3)
    cs = CollectionSection(seed_cell=sc, number_of_cells=100, collector=cp)

    cs.run_model()
    tops = cs.get_tops()
    print(tops)
    df = pd.DataFrame({"Settled top": tops[0], "Bed top": tops[1]})
    fig = px.line(df)
    fig.write_html("first_figure.html", auto_open=True)
