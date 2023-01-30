import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


def plot_line(
    df: pd.DataFrame,
    x_axis: dict[str, str],
    y_axis: dict[str, str],
    col: dict[str, str],
    template: str,
    file_name: str = None,
):
    """
    Generate and save (optional only pass the file name as str) a lineplot
    for the df.

    df: the Dataframe
    x_axis: {"col_name": df.col, "xaxis_title": "str"}
    y_axis: {"col_name": df.col,  "yaxis_title": "str"}
    col: {"col_name": df.col,  "legend_title": "str"}
    template: choose str from [
                                  "ggplot2",
                                  "seaborn",
                                  "simple_white",
                                  "plotly",
                                  "plotly_white",
                                  "plotly_dark",
                                  "presentation",
                                  "xgridoff",
                                  "ygridoff",
                                  "gridon",
                                  "none",
                              ]
    file_name: filename as str without suffix
    """

    fig = px.line(
        df,
        x=x_axis["col_name"],
        y=y_axis["col_name"],
        color=col["col_name"],
        hover_name="Squad",
    )
    fig.update_layout(
        xaxis_title=x_axis["xaxis_title"],
        yaxis_title=y_axis["yaxis_title"],
        legend_title=col["legend_title"],
        template=template,
    )
    fig.show()
    if file_name:
        full_path = f"./assets/line_plots/{file_name}.html"
        fig.write_html(full_path)
