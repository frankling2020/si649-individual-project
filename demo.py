import altair as alt
from vega_datasets import data
import pandas as pd

import streamlit as st

## Load data
@st.cache
def load_data():
    states = alt.topo_feature(data.us_10m.url, 'states')
    cost_disability = pd.read_csv('https://raw.githubusercontent.com/frankling2020/UMSI-Projects/main/cost_disability.csv')
    health_conditions = pd.read_csv('disease.csv')
    health_conditions['disability'] = health_conditions['disability'].map({1: "with", 0: "without"})
    return states, cost_disability, health_conditions


## Load data
states, cost_disability, health_conditions = load_data()

## Preprocessing
## State and ID mapping
state_names = cost_disability['LocationDesc'].copy()
state_ids = cost_disability['id'].copy()
state_ids = sorted(state_ids, key=lambda x: state_names[cost_disability['id'] == x].values[0])
state_names = sorted(state_names)


# Visualization 1: interactive
## Select state
viz_sel = alt.selection_single(
    fields = ['id'], 
    empty = 'all',
    on = 'dblclick',
    bind = alt.binding_select(
        options = [None] + state_ids,
        labels = ['All'] + state_names,
        name = 'Select State'
    )
)

## Base map
fig1_base = alt.Chart(states).mark_geoshape(
    stroke='white'
).project(
    type = 'albersUsa',
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(cost_disability, 'id', ['LocationDesc', 'disability_rate', 'cost_rate'])
)

## Layered map
fig1 = fig1_base.encode(
    color = alt.Color(
        'disability_rate:Q',
        bin=alt.BinParams(maxbins=5),
        title='Disability Rate'
    ),
    opacity = alt.condition(viz_sel , alt.value(1.0), alt.value(0.2)),
    tooltip=['LocationDesc:N', 'disability_rate:Q', 'cost_rate:Q'],
).properties(
    title = alt.TitleParams(
        text = 'Disability status among adults 18 years of age or older in each state',
        fontSize = 16,
    ),
)

fig2_base = alt.Chart(cost_disability).encode(
    x = alt.X('cost_rate:Q', axis=alt.Axis(title='Rate')),
    y = alt.Y('LocationDesc:N', sort=alt.EncodingSortField(field='cost_rate', op='sum', order='descending')),
)    
    
fig2 = fig2_base.mark_bar().encode(
    opacity = alt.condition(viz_sel, alt.value(1.0), alt.value(0.2)),
    tooltip=['LocationDesc:N', 'disability_rate:Q', 'cost_rate:Q'],
).properties(
    title = alt.TitleParams(
        text = ['Could not see a doctor due to cost in the past 12 months', 'among adults 18 years of age or older'],
        fontSize = 16,
        anchor = 'middle',
    ),
)

text = fig2.mark_text(baseline='middle', dx=20, color='darkred').encode(
    text = alt.condition(viz_sel, alt.Text('cost_rate:Q', format='.1%'), alt.value(' ')),
    opacity = alt.condition(viz_sel, alt.value(1.0), alt.value(0)),
)

viz1 = (fig1 & (fig2 + text)).add_selection(viz_sel).properties(
    title = {
        'text': 'Disability Rate and Expenditure in US in 2020', 
        'fontSize': 20, 
        'fontWeight': 'bold',
    },
).resolve_scale(x='shared')


# Visualization 2: interactive
## Layered bar chart
base_bar = alt.Chart(health_conditions).encode(
    y = alt.Y('disability:N', title=None),
)

bars = base_bar.mark_bar().encode(
    x = alt.X('value:Q'),
    color = alt.Color('disability:N'),
)

confidence_interval = base_bar.mark_errorbar(extent='ci', color='darkred').encode(
    x=alt.X('ci1:Q', title='Rate'),
    x2='ci2:Q',
)

annotation = base_bar.mark_text(align='left', dx=10).encode(
    x = alt.X('value:Q'),
    text = alt.Text('value:Q', format='.1%')
)

viz2 = (bars + confidence_interval + annotation).facet(
    row = alt.Row(
        'disease:N', 
        header=alt.Header(title='Health Conditions', labelOrient='top', titleFontSize=13),
        sort = alt.EncodingSortField(field='value', op='max', order='descending')),
).properties(
    title = alt.TitleParams(
        "Health Conditions among Adults w/o Disability in US in 2020",
        fontSize = 20,
        fontWeight = 'bold',
    )
)


# Streamlit
st.sidebar.title('Health Conditions of Disability and Barriers of Health Care in US in 2020')
st.sidebar.write(
    """
        One of the most basic things people with disabilities are asking for is respect. The
    biggest finding of the 2021 survey, Iezzoni says, is that doctors don't realize that the
    proper way to determine what accommodations a facility needs for patients with
    disabilities is to just ask the patients.
    "I can't tell you how many times I go to a doctor's office and I'm talking, but they're
    not hearing anything,” Salentine says. "They're ready to speak over me.”
    """
)



tab1, tab2 = st.tabs(['Health Conditions', 'Barriers of Health Care'])

with tab1:
    tab1.write(
        """
        Thee Department of Health and Human Services is aware of the issue. In a response to
        emailed questions, an HHS spokesperson wrote, "While we recognize the progress of
        the ADA, important work remains to uphold the rights of people with disabilities."
        The Office of Civil Rights, the spokesperson continued, "has taken a number of
        important actions to ensure that health care providers do not deny health care to
        individuals on the basis of disability and to guarantee that people with disabilities
        have full access to reasonable accommodations when receiving health care and human
        services, free of discriminatory barriers and bias."
        """
    )
    st.altair_chart(viz2, use_container_width=True)

with tab2:
    tab2.write(
        """
        Eventually, the patient's adult daughter told Lagu
        that she hadn't been able to find a specialist who would see a patient in a
        wheelchair. Incredulous, Lagu started making calls. "I could not find that
        kind of doctor within 100 miles of her house who would see her," she
        says, "unless she came in an ambulance and was transferred to an
        exam table by EMS—which would have cost her family more than
        $1,000 out of pocket."
        """
    )
    st.altair_chart(viz1, use_container_width=True)
