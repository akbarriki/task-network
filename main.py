import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import gnet
import numpy as np
from pyvis.network import Network

def getDisplay(subdit=None, seksi=None, idpegawai=[], tasks=[]):
    net = Network(height='400px', width="100%", bgcolor='#FFFFFF', font_color='black')
    if not subdit:
        net = gnet.graphOverviewTIK(df_pegawai, df_task_pegawai, net)
    elif subdit and not idpegawai:
        net = gnet.graphUnitTIK(df_pegawai, df_task_pegawai, subdit, seksi, net)
    else:
        net = gnet.graphPegawaiTIK(df_pegawai, df_task_pegawai, subdit, seksi, idpegawai, net)
    
    net.save_graph('html_files/tab1.html')
    HtmlFile = open('html_files/tab1.html', 'r', encoding='utf-8')
    return HtmlFile

def getDisplayTask(tasks='all'):
    global df_pegawai, df_task_pegawai
    net = Network(height='400px', width="100%", bgcolor='#FFFFFF', font_color='black')
    if tasks or tasks == 'all':
        net = gnet.graphTaskTIK(df_pegawai, df_task_pegawai, tasks, net)
        net.save_graph('html_files/tab1.html')
        HtmlFile = open('html_files/tab1.html', 'r', encoding='utf-8')
        return HtmlFile
    return ""
    

def createHorizontalBar(df, subdit=None, seksi=None):
    ind = np.arange(len(df))
    width = 0.45
    fig, ax = plt.subplots(figsize=(8, 8))
    plt.rcParams.update({'font.size':16})
    recs_tusi = ax.barh(ind, df.tusi, width, color='#758FD5', label='Tusi')
    recs_adhoc = ax.barh(ind + width, df.adhoc, width, color='#D44D4D', label='Adhoc')
    def autolabel(recs):
        for rec in recs:
            width = rec.get_width()
            plt.text(0.95*rec.get_width(), rec.get_y()+0.5*rec.get_height(),
                    '%d' % int(width),
                    ha='center', va='center', color='white')

    autolabel(recs_tusi)
    autolabel(recs_adhoc)

    if not subdit:
        labels = [f"Subdit {idx}" for idx in list(df.index)]
    elif subdit and not seksi:
        labels = [f"Seksi {idx}" for idx in list(df.index)]
    elif subdit and seksi:
        labels = [idx[:idx.find("(")].strip() for idx in list(df.index)]

    
    ax.set(yticks=ind + width, yticklabels=labels, ylim=[2*width - 1, len(df)])
    plt.tick_params(
        axis='x',          # changes apply to the x-axis
        which='both',      # both major and minor ticks are affected
        bottom=False,      # ticks along the bottom edge are off
        top=False,         # ticks along the top edge are off
        labelbottom=False) # labels along the bottom edge are off
    ax.legend()
    # plt.show()
    plt.title("Distribusi Pekerjaan (Tusi dan Adhoc)")
    plt.savefig('overviewTIK.png')
    st.image('overviewTIK.png')


# Read dataset (CSV)
df_pegawai = pd.read_csv('data/pegawai.csv', sep=",")
df_task_pegawai = pd.read_csv('data/task_pegawai.csv', sep=",")

# Set header title
page_title = "TIK Task Network"
st.set_page_config(page_title=page_title, page_icon=None, layout="wide")
st.title(page_title)
st.markdown(f"""
    <style>
        .css-z5fcl4{{
            padding: 1rem 1rem 1rem;
        }}
        h1 {{
            font-size: calc(1rem + 1.8vw);
        }}
    </style>""",
    unsafe_allow_html=True,
)

    
col1, col2, col3 = st.columns((1,2,1))
with col1:
    # subdit = st.radio("Subdit", subdit_set, horizontal=True)
    subdit = st.selectbox("Subdit", gnet.getUnitList(df_pegawai, level='subdit'), placeholder="Pilih Subdit")
    seksi = st.selectbox('Seksi', gnet.getUnitList(df_pegawai, level='seksi', upperUnit=subdit), placeholder="Pilih Seksi")
    pegawai = st.multiselect('Pegawai', gnet.getPegawaiList(df_pegawai, subdit=subdit, seksi=seksi), placeholder="Pilih Pegawai")
    tasks = st.multiselect('Rumpun Pekerjaan', gnet.getTaskList(df_task_pegawai), placeholder="Pilih Pekerjaan")


if subdit == "all":
    subdit = None
if seksi == "all":
    seksi = None

if tasks == "all" or tasks:
    HtmlFile = getDisplayTask(tasks)
else:
    HtmlFile = getDisplay(subdit, seksi, pegawai, tasks)


with col2:
    components.html(HtmlFile.read(), height=450)
with col3:
    if tasks == "all" or tasks:
        pass
    else:
        df = pd.DataFrame(gnet.statTaskByUnit(df_pegawai, df_task_pegawai, subdit=subdit, seksi=seksi)).T        
        createHorizontalBar(df, subdit, seksi)
