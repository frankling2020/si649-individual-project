"""SI649 Individual Project
unique name: hyfrankl
Link: https://hyfrankl-si649-individual-project.streamlit.app/

Usage: streamlit run demo.py
Description: Interactive visualization of health conditions of disability and barriers of health care in US in 2020.
Interaction: see the description of the expander in the "Barriers of Health Care" section.
"""


import altair as alt
from vega_datasets import data
import pandas as pd

import streamlit as st

## Load data
@st.cache
def load_data():
    ## Load data
    states = alt.topo_feature(data.us_10m.url, 'states')
    cost_disability = pd.read_csv('cost_disability.csv')
    health_conditions = pd.read_csv('disease.csv')
    health_conditions['disability'] = health_conditions['disability'].map({1: "Disabled", 0: "Non-disabled"})
    
    ## Preprocessing
    ## State and ID mapping
    cost_disability['dis_rank'] = cost_disability['disability_rate'].rank(ascending=False)
    state_names = cost_disability['LocationDesc'].copy()
    state_ids = cost_disability['id'].copy()
    state_ids = sorted(state_ids, key=lambda x: state_names[cost_disability['id'] == x].values[0])
    state_names = sorted(state_names)
    cost_rate_max = max(cost_disability['cost_rate'])
    cost_rate_min = min(cost_disability['cost_rate'])
    
    return states, cost_disability, health_conditions, state_names, state_ids, cost_rate_max, cost_rate_min


## Load data
states, cost_disability, health_conditions, state_names, state_ids, cost_rate_max, cost_rate_min = load_data()


## Sidebar
with st.sidebar:
    st.title('Health Conditions of Disability and Barriers of Health Care in US in 2020')


    st.markdown(
        """
        People with disabilities are suffering many health problems while having less access to health care 
        and worse treatment from doctors than their non-disabled counterparts. These visualizations show the health conditions of disability and
        barriers of health care in US in 2020. As mentioned in the article,
        """,
        unsafe_allow_html=True
    )
    
    st.image('font.jpeg',
    caption='''People with disabilities
        get preventive care less frequently and have worse outcomes than their non-disabled
        counterparts. [1]''')

    with st.expander("__Reference__"):
        st.markdown("""
            [1] Sohn, R. (2022, February 28). Large majority of doctors hold misconceptions about people with disabilities, survey finds. [STAT](https://www.statnews.com/2021/02/01/large-majority-of-doctors-hold-misconceptions-about-people-with-disabilities-survey-finds/).
                
            <a id="2"> [2]</a> Yasinski, E. (2022, December 15). Doctors Are Failing Patients With Disabilities. [The Atlantic](https://www.theatlantic.com/health/archive/2022/11/disability-health-care-accessibility-doctors-ada/672101/).
            """,
            unsafe_allow_html=True
        )


# Visualization 1: interactive
def viz1(nearby_state):
    viz_sel = alt.selection_single(
        fields = ['id'], 
        empty = 'all',
    )

    ## Base map
    fig1_base = alt.Chart(states).mark_geoshape(
        stroke='white'
    ).project(
        type = 'albersUsa',
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(cost_disability, 'id', ['LocationDesc', 'disability_rate', 'cost_rate', 'dis_rank'])
    )

    if agree:
        select_state_rank = cost_disability['dis_rank'][cost_disability['id'] == state_selector].values[0] if agree else -1
        slider_condition = abs(alt.datum.dis_rank - select_state_rank) <= nearby_state
    else:
        slider_condition =  alt.datum.cost_rate >= slider
    
    op_condition = alt.condition(viz_sel, alt.value(1.0), alt.value(0.2))
    color_bins = alt.Color('disability_rate:Q', bin=alt.BinParams(maxbins=5), title='Disability Rate')
    color_condition = alt.condition(slider_condition, color_bins, alt.value('lightgray'))

    ## Layered map
    fig1 = fig1_base.encode(
        color = color_condition,
        opacity = op_condition,
        tooltip=['LocationDesc:N', 'disability_rate:Q', 'cost_rate:Q'],
    ).properties(
        title = alt.TitleParams(
            text = 'Disability status among adults 18 years of age or older in each state',
            fontSize = 16,
        ),
    )

    fig2_base = alt.Chart(cost_disability).encode(
        x = alt.X('cost_rate:Q', axis=alt.Axis(title='Rate')),
        y = alt.Y('LocationDesc:N', title=None,
            sort=alt.EncodingSortField(field='cost_rate', op='sum', order='descending')),
    ).transform_filter(
        slider_condition
    )
        
    fig2 = fig2_base.mark_bar().encode(
        opacity = op_condition,
        tooltip=['LocationDesc:N', 'disability_rate:Q', 'cost_rate:Q'],
    ).properties(
        title = alt.TitleParams(
            text = ['Could not see a doctor due to cost in the past 12 months', 
                'among adults 18 years of age or older in each state'],
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
    return viz1


# Visualization 2: interactive
def viz2():
    ## Layered bar chart
    base_bar = alt.Chart(health_conditions).encode(
        x = alt.X('disability:N', title=None, axis=None),
    )

    bars = base_bar.mark_bar().encode(
        y = alt.Y('value:Q'),
        color = alt.Color('disability:N', legend=alt.Legend(title='Disability Status')),
    )

    confidence_interval = base_bar.mark_errorbar(extent='ci', color='darkred').encode(
        y=alt.Y('ci1:Q', title='Rate'),
        y2=alt.Y2('ci2:Q', title=None),
    )

    annotation = base_bar.mark_text(align='center', dy=-12, size=9, color='darkred').encode(
        y = alt.Y('value:Q'),
        text = alt.Text('value:Q', format='.1%'),
    )

    viz2 = (bars + confidence_interval + annotation).facet(
        column = alt.Column(
            'disease:N', 
            header = alt.Header(title=None, labelOrient='top', titleFontSize=15),
            sort = alt.EncodingSortField(field='value', op='max', order='descending')),
        spacing = 30,
    ).properties(
        title = alt.TitleParams(
            "Health Conditions among Adults related to Disability in US in 2020",
            fontSize = 20,
            fontWeight = 'bold',
        )
    )
    return viz2


# Streamlit
if "email" in st.experimental_user:
    st.write(f"Hi, {st.experimental_user['email']}!")

tab1, tab2 = st.tabs(['Health Conditions', 'Barriers of Health Care'])

with tab1:
    tab1.markdown('### Uphold the Rights of People with Disabilities to Access Health Care')
    tab1.write(
        """
        It is essential that healthcare providers recognize the unique healthcare needs of individuals with 
        disabilities and work to ensure that they receive the same level of care and access to services as 
        non-disabled individuals. The visualization demonstrates that individuals with disabilities are more likely 
        to suffer from health issues than their non-disabled counterparts. While the ADA has made great strides,
        people with disabilities, more prone to health problems, are still facing discriminatory barriers and bias.
        """
    )
    tab1.write(
    """
    ------
    _One of the most basic things people with disabilities are asking for is respect... 
    "I can't tell you how many times I go to a doctor's office and I'm talking, but they're not hearing anything,” 
    Salentine says. "They're ready to speak over me."* [[2]](#2)_
    """)
    tab1.write("------")
    viz2 = viz2()
    st.altair_chart(viz2, use_container_width=True)
    

with tab2:
    tab2.markdown('### Barriers of Health Care')
    tab2.write("""
        As stated in the article, people with disabilities have lower incomes, and some individuals may
        not call for an ambulance due to financial constraints. The slider allows users to select states
        with a higher ratio of individuals facing expenditure issues. It aims to drawing attention to
        regions such as the southern and southeastern parts of America where healthcare
        expenditure is a significant issue for locals.
    """)
    tab2.write("""
        ------
        _Eventually, the patient's adult daughter told Lagu
        that she hadn't been able to find a specialist who would see a patient in a
        wheelchair. Incredulous, Lagu started making calls. "I could not find that
        kind of doctor within 100 miles of her house who would see her," she
        says, "unless she came in an ambulance and was transferred to an
        exam table by EMS—which would have cost her family more than
        $1,000 out of pocket." [[2]](#2)_
    """)
    tab2.write("------")


    with st.expander("How to use this visualization?"):
        st.write('''
        This visualization shows the relationship between disability rate and expenditure
        in each state. There are two modes for this interactive visualizations. By default, the slider is enabled. 
        You can switch the mode by the check box below.
        
        In the slider mode, you will see a lower bound of expenditure issue, which will help you find some geographical patterns. 
        In the state selector mode, you will see the states that share similar disability rate, while they may not share similar expenditure issue.
        It is time to reflect on the data!
        ''')
        agree = st.checkbox('Disable slider to select state')
        
    if agree:
        state_selector = st.selectbox('Select State', state_ids, format_func=lambda x: state_names[state_ids.index(x)])
    else:
        slider = tab2.slider('Select Lower Bound of Expenditure Issue', 
        cost_rate_min, cost_rate_max, (cost_rate_min + cost_rate_max)/2, 0.01)
    viz1 = viz1(nearby_state=4)
    st.altair_chart(viz1, use_container_width=True)
