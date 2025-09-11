import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(
    page_title="US Population Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

st.markdown("""
<style>
:root { --card-bg:#2f2f2f; --card-br:16px; --card-pad:18px; }

[data-testid="block-container"]{
  padding: 1rem 2rem 0rem 2rem;
}
section.main > div { gap: 1rem !important; }

.header-bar{
  background: var(--card-bg);
  border-radius: var(--card-br);
  padding: 14px 18px;
  margin-bottom: 8px;
  display:flex; align-items:center; justify-content:space-between;
}

.kpi{
  background: var(--card-bg);
  border-radius: var(--card-br);
  padding: var(--card-pad);
}

[data-testid="stMetric"]{
  background: transparent;
  text-align:center;
  padding: 8px 0 0 0;
}

/* Fix delta pill + arrow overlap and spacing */
[data-testid="stMetricDelta"]{
  display:inline-flex; align-items:center; gap:6px;
}
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"]{
  position: static; left:auto; transform:none; margin-right:0;
}

/* Sidebars a bit tighter */
[data-testid="stSidebarNav"] + div [data-testid="stVerticalBlock"]{
  gap: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

df_reshaped = pd.read_csv('data/us-population-2010-2019-reshaped.csv')
MIGRATION_THRESHOLD = 100_000

with st.sidebar:
    st.title("US Population")
    year_list = list(df_reshaped.year.unique())[::-1]
    selected_year = st.selectbox("Year", year_list)

    st.markdown("**Display**")
    color_theme_list = ['viridis', 'cividis', 'magma', 'plasma', 'inferno']
    selected_color_theme = st.selectbox("Color theme", color_theme_list, index=0)

    st.markdown("**Analysis**")
    MIGRATION_THRESHOLD = st.number_input(
        "Migration threshold", min_value=10_000, max_value=1_000_000,
        step=10_000, value=100_000, help="Used for inbound/outbound donut stats"
    )

def make_us_trend(df, metric="total"):
    nat = (df.groupby('year', as_index=False)
             .agg(total_pop=('population', 'sum'),
                  mean_pop=('population', 'mean'),
                  median_pop=('population', 'median')))

    titles = {
        "total":  "U.S. population (total)",
        "mean":   "Average population per state",
        "median": "Median population per state",
    }
    col_map = {"total": "total_pop", "mean": "mean_pop", "median": "median_pop"}
    ycol = col_map[metric]
    title = titles[metric]

    chart = (alt.Chart(nat)
             .mark_line(point=True)
             .encode(
                 x=alt.X('year:O', title='Year'),
                 y=alt.Y(f'{ycol}:Q', title=title),
                 tooltip=[alt.Tooltip('year:O', title='Year'),
                          alt.Tooltip(f'{ycol}:Q', title=title, format=',')]
             )
             .properties(height=300, width=900))
    return chart

    
def make_choropleth(input_df, input_id, input_column, input_color_theme):
    choropleth = px.choropleth(input_df, locations=input_id, color=input_column, locationmode="USA-states",
                               color_continuous_scale=input_color_theme,
                               range_color=(0, max(df_selected_year.population)),
                               scope="usa",
                               labels={'population':'Population'}
                              )
    choropleth.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return choropleth

def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          domain=[input_text, ''],
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          domain=[input_text, ''],
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text
    
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

def calculate_population_difference(input_df, input_year):
  selected_year_data = input_df[input_df['year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
  selected_year_data['population_difference'] = selected_year_data.population.sub(previous_year_data.population, fill_value=0)
  return pd.concat([selected_year_data.states, selected_year_data.id, selected_year_data.population, selected_year_data.population_difference], axis=1).sort_values(by="population_difference", ascending=False)
    
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
    st.markdown('#### Gains/Losses')

    df_population_difference_sorted = calculate_population_difference(df_reshaped, selected_year)

    if selected_year > 2010:
        first_state_name = df_population_difference_sorted.states.iloc[0]
        first_state_population = format_number(df_population_difference_sorted.population.iloc[0])
        first_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[0])
    else:
        first_state_name = '-'
        first_state_population = '-'
        first_state_delta = ''
    st.metric(label=first_state_name, value=first_state_population, delta=first_state_delta)

    if selected_year > 2010:
        last_state_name = df_population_difference_sorted.states.iloc[-1]
        last_state_population = format_number(df_population_difference_sorted.population.iloc[-1])   
        last_state_delta = format_number(df_population_difference_sorted.population_difference.iloc[-1])   
    else:
        last_state_name = '-'
        last_state_population = '-'
        last_state_delta = ''
    st.metric(label=last_state_name, value=last_state_population, delta=last_state_delta)
    
    st.markdown('#### States Migration')

    if selected_year > 2010:
        df_greater = df_population_difference_sorted[df_population_difference_sorted.population_difference > MIGRATION_THRESHOLD]
        df_less = df_population_difference_sorted[df_population_difference_sorted.population_difference < -MIGRATION_THRESHOLD]

        
        states_migration_greater = round((len(df_greater) / df_population_difference_sorted.states.nunique()) * 100)
        states_migration_less    = round((len(df_less)    / df_population_difference_sorted.states.nunique()) * 100)
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')
    else:
        states_migration_greater = 0
        states_migration_less = 0
        donut_chart_greater = make_donut(states_migration_greater, 'Inbound Migration', 'green')
        donut_chart_less = make_donut(states_migration_less, 'Outbound Migration', 'red')

    migrations_col = st.columns((0.2, 1, 0.2))
    with migrations_col[1]:
        st.write('Inbound')
        st.altair_chart(donut_chart_greater)
        st.write('Outbound')
        st.altair_chart(donut_chart_less)

with col[1]:
    st.markdown('#### Total Population')
    
    choropleth = make_choropleth(df_selected_year, 'states_code', 'population', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)
    
    st.markdown('#### U.S. Trend')
    st.altair_chart(make_us_trend(df_reshaped, "total"), use_container_width=True)
    
with col[2]:
    st.markdown('#### Top States')
    
    st.dataframe(
        df_selected_year_sorted,
        column_order=("states", "population"),
        hide_index=True,
        use_container_width=True,   # ✅ fill the column
        column_config={
            "states": st.column_config.TextColumn("States"),
            "population": st.column_config.ProgressColumn(
                "Population",
                format="%d",                      # population is an integer
                min_value=0,
                max_value=int(df_selected_year_sorted.population.max()),
            ),
        },
    )

    with st.expander('About', expanded=True):
        st.write("""
        - :orange[**States Migration**]: percentage of states with annual inbound/outbound migration > Migration Threshold (Value from filter on left)
        """)




