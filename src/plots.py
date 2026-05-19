import pandas as pd
import plotly.graph_objects as go


def create_dose_response_plot(summary_df: pd.DataFrame, fit_curve_df: pd.DataFrame | None = None):
    fig = go.Figure()

    for drug_name, group in summary_df.groupby("drug_name"):
        plot_group = group.copy()
        plot_group["plot_concentration"] = plot_group["concentration_uM"].replace(0, 0.001)

        fig.add_trace(
            go.Scatter(
                x=plot_group["plot_concentration"],
                y=plot_group["mean_viability"],
                mode="lines+markers",
                name=str(drug_name),
                error_y=dict(
                    type="data",
                    array=plot_group["sem_viability"],
                    visible=True,
                ),
                customdata=plot_group[
                    ["concentration_uM", "sd_viability", "sem_viability", "n"]
                ],
                hovertemplate=(
                    "Drug: " + str(drug_name) + "<br>"
                    "Concentration: %{customdata[0]} uM<br>"
                    "Mean viability: %{y:.2f}%<br>"
                    "SD: %{customdata[1]:.2f}<br>"
                    "SEM: %{customdata[2]:.2f}<br>"
                    "n: %{customdata[3]}<extra></extra>"
                ),
            )
        )

    if fit_curve_df is not None and not fit_curve_df.empty:
        for drug_name, group in fit_curve_df.groupby("drug_name"):
            fig.add_trace(
                go.Scatter(
                    x=group["concentration_uM"],
                    y=group["predicted_viability"],
                    mode="lines",
                    name=f"{drug_name} IC50 fit",
                    line=dict(dash="dash"),
                    hovertemplate=(
                        "Drug fit: " + str(drug_name) + "<br>"
                        "Concentration: %{x:.3g} uM<br>"
                        "Predicted viability: %{y:.2f}%<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        title="Dose-Response Curve",
        xaxis_title="Concentration (uM, log scale; 0 plotted as 0.001)",
        yaxis_title="Mean Cell Viability (%)",
        template="plotly_white",
        hovermode="closest",
    )

    fig.update_xaxes(type="log")
    return fig
