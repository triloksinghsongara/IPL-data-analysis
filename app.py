from flask import Flask, render_template
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot

app = Flask(__name__)

# ------------------------------------------------------------
# Load Data
# ------------------------------------------------------------
def load_data():
    matches = pd.read_csv("data/matches.csv")
    deliveries = pd.read_csv("data/deliveries.csv")
    return matches, deliveries

# ------------------------------------------------------------
# ANALYTICS FUNCTIONS
# ------------------------------------------------------------
def summary_stats(matches, deliveries):
    stats = {}
    stats['total_matches'] = matches.shape[0]
    stats['total_seasons'] = matches['season'].nunique()

    # FIXED append() -> concat()
    stats['total_teams'] = pd.concat([matches['team1'], matches['team2']]).nunique()

    stats['total_players_estimated'] = deliveries['batter'].nunique()
    return stats


def top_scorers(deliveries, top_n=10):
    runs_by_player = deliveries.groupby('batter')['batsman_runs'].sum()
    runs_by_player = runs_by_player.sort_values(ascending=False)
    df = runs_by_player.reset_index().rename(columns={'batsman_runs': 'runs'})
    return df.head(top_n)


def top_wicket_takers(deliveries, top_n=10):
    wicket_data = deliveries[
        deliveries['player_dismissed'].notna() &
        (deliveries['dismissal_kind'] != 'run out')
    ]

    wk = wicket_data.groupby('player_dismissed').size().sort_values(ascending=False)
    df = wk.reset_index().rename(columns={0: 'wickets', 'player_dismissed': 'player'})
    return df.head(top_n)


def team_wins_by_season(matches, season=None):
    df = matches.copy()
    if season:
        df = df[df['season'] == season]

    wins = df.groupby('winner').size().sort_values(ascending=False)
    return wins.reset_index().rename(columns={0: 'wins', 'winner': 'team'})


# ------------------------------------------------------------
# PLOT FUNCTIONS (Plotly)
# ------------------------------------------------------------
def bar_plot_top_scorers(df):
    trace = go.Bar(x=df['batter'].tolist(), y=df['runs'].tolist())
    layout = go.Layout(
        title='Top Run Scorers',
        xaxis=dict(title='Player'),
        yaxis=dict(title='Runs')
    )
    fig = go.Figure([trace], layout)
    return plot(fig, output_type="div", include_plotlyjs=False)


def bar_plot_top_wickets(df):
    trace = go.Bar(x=df['player'].tolist(), y=df['wickets'].tolist())
    layout = go.Layout(
        title='Top Wicket Takers',
        xaxis=dict(title='Player'),
        yaxis=dict(title='Wickets')
    )
    fig = go.Figure([trace], layout)
    return plot(fig, output_type="div", include_plotlyjs=False)


def line_team_wins_over_seasons(matches):
    df = matches.copy()
    wins = df.groupby(['season', 'winner']).size().reset_index(name='wins')

    pivot = wins.pivot(index='season', columns='winner', values='wins').fillna(0)

    # TOP 6 TEAMS
    top_teams = pivot.sum().sort_values(ascending=False).head(6).index.tolist()

    traces = []
    for team in top_teams:
        traces.append(
            go.Scatter(
                x=pivot.index.tolist(),
                y=pivot[team].tolist(),
                mode='lines+markers',
                name=team
            )
        )

    layout = go.Layout(
        title='Wins by Season (Top 6 Teams)',
        xaxis=dict(title='Season'),
        yaxis=dict(title='Wins')
    )

    fig = go.Figure(traces, layout)
    return plot(fig, output_type="div", include_plotlyjs=False)


# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.route("/")
def index():
    matches, deliveries = load_data()

    stats = summary_stats(matches, deliveries)
    top_runs = top_scorers(deliveries)
    top_wk = top_wicket_takers(deliveries)
    team_wins = team_wins_by_season(matches)

    runs_div = bar_plot_top_scorers(top_runs)
    wk_div = bar_plot_top_wickets(top_wk)
    wins_season_div = line_team_wins_over_seasons(matches)

    return render_template(
        "index.html",
        stats=stats,
        runs_graph=runs_div,
        wk_graph=wk_div,
        wins_season_graph=wins_season_div,
        top_runs_table=top_runs.to_html(classes='table table-striped', index=False),
        top_wk_table=top_wk.to_html(classes='table table-striped', index=False),
        team_wins_table=team_wins.to_html(classes='table table-striped', index=False)
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
