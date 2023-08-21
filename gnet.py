import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from pyvis.network import Network

graphDefaultConfig = {
    'node_distance':90, 'central_gravity':0.9, 'spring_length':80, 
    'spring_strength':0.10, 'damping':0.95
}
   
def getNamaPegawai(df, idpegawai):
    return list(df[df['idpegawai'] == idpegawai]['namapegawai'])[0]

def statTaskByUnit(df_pegawai, df_task_pegawai, subdit=None, seksi=None):
    if not subdit and not seksi:
        merge_ = pd.merge(df_pegawai, df_task_pegawai, on="idpegawai", how="left").dropna().groupby(['subdit', 'jenistask']).agg('count').reset_index()[['subdit','jenistask','task']]
        dct = {subd:{"adhoc":0, "tusi":0} for subd in merge_.subdit.unique()}
        for i,row in merge_.iterrows():
            dct[row['subdit']][row['jenistask']] = row['task']
        return dct
        
    if seksi:
        merge_ = pd.merge(df_pegawai[(df_pegawai["subdit"] == subdit) & (df_pegawai["seksi"] == seksi)], df_task_pegawai, on="idpegawai", how="left").dropna().groupby(['idpegawai','jenistask']).agg('count').reset_index()[['idpegawai','jenistask','task']]
        dct = {idpegawai:{"adhoc":0, "tusi":0} for idpegawai in merge_.idpegawai.unique()}
        for i,row in merge_.iterrows():
            dct[row['idpegawai']][row['jenistask']] = row['task']
        return {f'{getNamaPegawai(df_pegawai, k)} ({k})':v for k,v in dct.items()}
    
    if subdit:
        merge_ = pd.merge(df_pegawai[df_pegawai["subdit"] == subdit], df_task_pegawai, on="idpegawai", how="left").dropna().groupby(['seksi','jenistask']).agg('count').reset_index()[['seksi','jenistask','task']]
        dct = {seksi:{"adhoc":0, "tusi":0} for seksi in merge_.seksi.unique()}
        for i,row in merge_.iterrows():
            dct[row['seksi']][row['jenistask']] = row['task']
        return dct

def statTaskByPegawai(df_pegawai, df_task_pegawai, subdit=None, seksi=None, idpegawai=[]):
     filter = df_pegawai['jabatan'] != 'kasi'
     if subdit:
         filter &= df_pegawai['subdit'] == subdit
     if seksi:
         filter &= df_pegawai['seksi'] == seksi
     if idpegawai:
         if 'all' in idpegawai:
             pass
         else:
             idpegawai = [peg[peg.find("("):].replace("(","").replace(")","").strip() for peg in idpegawai]
             filter &= df_pegawai['idpegawai'].isin(idpegawai)
     merge_ = pd.merge(df_pegawai[filter], df_task_pegawai, 
                       on="idpegawai", how="left")[['idpegawai','namapegawai','task']].apply(
                        lambda x: [f"{x['namapegawai']} ({x['idpegawai']})", x['task']]
                    ,axis=1)
     merge_ = list(merge_)
     pegawai_nodes = list(set([m[0] for m in merge_]))
     task_nodes = list(set([m[1] for m in merge_ if str(m[1]) != 'nan']))
     edges = [m for m in merge_ if str(m[1]) != "nan"]
     return pegawai_nodes, task_nodes, edges

def statPegawaiByTask(df_task_pegawai, idpegawai):
    try:
        return list(df_task_pegawai[df_task_pegawai['idpegawai'] == idpegawai].idpegawai.value_counts())[0]
    except:
        return 0

def statTaskByNumPegawai(df_task_pegawai, task=None):
    try:
        if task:
          return list(df_task_pegawai[df_task_pegawai['task'] == task].task.value_counts())[0]
        else:
          return df_task_pegawai.task.value_counts().to_dict()
    except:
        return 0

def getUnitList(df, level='subdit', upperUnit=None):
    if level == 'subdit':
        return tuple(['all'] + list(df[level].unique()))
    if level == 'seksi' and upperUnit:
        return tuple(['all']+list(df[df['subdit'] == upperUnit][level].unique()))

def getPegawaiList(df, subdit=None, seksi=None):
    if subdit:
        filter = (df['subdit'] == subdit) & (df['jabatan'] != 'kasi')
        if seksi and seksi != "all":
            filter &= (df['seksi'] == seksi)
        else:
            pass
        listpegawai = df[filter][['idpegawai', 'namapegawai']].apply(lambda x: f"{x['namapegawai']} ({x['idpegawai']})", axis=1)
        listpegawai = ['all']+list(listpegawai)
        return listpegawai
    return []

def getTaskList(df):
    return ['all'] + list(df.task.unique())

def getAllTasks(df_pegawai, df_task_pegawai, tasks=[]):
    if 'all' in tasks or not tasks:
        pass
    else:
        # idpegawai = [peg[peg.find("("):].replace("(","").replace(")","").strip() for peg in idpegawai]
        filter = df_task_pegawai['task'].isin(tasks)
        df_task_pegawai = df_task_pegawai[filter]
    merge_ = pd.merge(df_task_pegawai, df_pegawai, 
                    on="idpegawai", how="left").apply(
                        lambda x: [f"{x['namapegawai']} ({x['idpegawai']})", x['jenistask'], x['subdit'], x['seksi'], x['task']]
                    ,axis=1)
    merge_ = list(merge_)
    
    pegawai_nodes = list(set([(m[0], m[2], m[3]) for m in merge_]))
    task_nodes = list(set([m[-1] for m in merge_ if str(m[-1]) != 'nan']))
    edges = [[m[0], m[-1]] for m in merge_ if str(m[-1]) != "nan"]
    return pegawai_nodes, task_nodes, edges
    
def graphOverviewTIK(df_pegawai, df_task_pegawai, net=None):
    data = statTaskByUnit(df_pegawai, df_task_pegawai)
    total_tusi, total_adhoc, total_task = 0,0,0
    edges = []
    centre_node = "Dit.TIK"
    for k,v in data.items():
        title = f"Subdit {k}\n\nTusi: {v['tusi']}\nAdhoc: {v['adhoc']}"
        label = f"Subdit {k}"
        value = v['adhoc'] + v['tusi']

        total_tusi += v['tusi']
        total_adhoc += v['adhoc']
        total_task += value
        
        net.add_node(str(k), title=title, label=label, shape="dot", value=value, color='green')
        edges.append([centre_node, str(k)])
    net.add_node(centre_node, title=f"Total rumpun pekerjaan: {total_task}\nTusi: {total_tusi}\nAdhoc: {total_adhoc}")
    net.add_edges(edges)

    node_distance, central_gravity, spring_length, spring_strength, damping = list(graphDefaultConfig.values())

    net.repulsion(node_distance=node_distance, central_gravity=central_gravity,
               spring_length=spring_length, spring_strength=spring_strength,
               damping=damping)
    
    return net

def graphUnitTIK(df_pegawai, df_task_pegawai, subdit=None, seksi=None, net=None):
    data = statTaskByUnit(df_pegawai, df_task_pegawai, subdit=subdit, seksi=seksi)
    total_tusi, total_adhoc, total_task = 0,0,0
    edges = []

    if subdit and not seksi:
        centre_node = f"Subdit {subdit}"
        for k,v in data.items():
            title = f"Seksi {k}\n\nTusi: {v['tusi']}\nAdhoc: {v['adhoc']}"
            label = f"Seksi {k}"
            value = v['adhoc'] + v['tusi']

            total_tusi += v['tusi']
            total_adhoc += v['adhoc']
            total_task += value

            net.add_node(str(k), title=title, label=label, shape="dot", value=value, color='#27E285')
            edges.append([centre_node, str(k)])
            centre_node_color = "green"

    elif subdit and seksi:
        centre_node = f"Seksi {seksi}"
        for k,v in data.items():
            namapegawai = k[:k.find("(")].strip()
            title = f"{k}\n\nTusi: {v['tusi']}\nAdhoc: {v['adhoc']}"
            label = f"{namapegawai}"
            value = v['adhoc'] + v['tusi']

            total_tusi += v['tusi']
            total_adhoc += v['adhoc']
            total_task += value

            net.add_node(str(k), title=title, label=label, shape="dot", value=value, color='#E26389')
            edges.append([centre_node, str(k)])
            centre_node_color = "#27E285"

    net.add_node(centre_node, title=f"Total rumpun pekerjaan: {total_task}\nTusi: {total_tusi}\nAdhoc: {total_adhoc}", color=centre_node_color)
    net.add_edges(edges)

    node_distance, central_gravity, spring_length, spring_strength, damping = list(graphDefaultConfig.values())

    net.repulsion(node_distance=node_distance, central_gravity=central_gravity,
               spring_length=spring_length, spring_strength=spring_strength,
               damping=damping)
    
    return net

def graphPegawaiTIK(df_pegawai, df_task_pegawai, subdit=None, seksi=None, idpegawai=[], net=None):
    pegawai_nodes, task_nodes, edges = statTaskByPegawai(df_pegawai, df_task_pegawai, 
                                                         subdit=subdit, seksi=seksi, idpegawai=idpegawai)
    
    for pn in pegawai_nodes:
        label = pn[:pn.find("(")].strip()
        net.add_node(pn, label=label, shape="dot",color='#E26389')
    
    for tn in task_nodes:
        label = tn
        net.add_node(tn, label=label, shape="dot",color='#E1EB53')
    
    net.add_edges(edges)
    node_distance, central_gravity, spring_length, spring_strength, damping = list(graphDefaultConfig.values())
    net.repulsion(node_distance=node_distance, central_gravity=central_gravity,
               spring_length=spring_length, spring_strength=spring_strength,
               damping=damping)
    
    return net

def graphTaskTIK(df_pegawai, df_task_pegawai, tasks=[], net=None):
    pegawai_nodes, task_nodes, edges = getAllTasks(df_pegawai, df_task_pegawai, tasks=tasks)
    
    for namanip, subdit, seksi in pegawai_nodes:
        nama = namanip[:namanip.find("(")].strip()
        label = f"{nama}\nSubdit:{subdit}\nSeksi:{seksi}"
        net.add_node(namanip, label=label, shape="dot",color='#E26389')
    
    for tn in task_nodes:
        label = tn
        net.add_node(tn, label=label, shape="dot",color='#E1EB53')
    
    net.add_edges(edges)

    node_distance, central_gravity, spring_length, spring_strength, damping = list(graphDefaultConfig.values())
    net.repulsion(node_distance=node_distance, central_gravity=central_gravity,
               spring_length=spring_length, spring_strength=spring_strength,
               damping=damping)
    
    return net

if __name__ == "__main__":

     df_pegawai = pd.read_csv("data/pegawai.csv", sep=",")
     df_task_pegawai = pd.read_csv("data/task_pegawai.csv", sep=",")

    #  print(df_pegawai.head())
    #  print()
    #  print(df_task_pegawai.head())

    #  test case

    #  print(statTaskByUnit(df_pegawai, df_task_pegawai))
    #  print() 

    #  print(statTaskByUnit(df_pegawai, df_task_pegawai, subdit=1, seksi=None))
    #  print()

    #  print(statTaskByUnit(df_pegawai, df_task_pegawai, subdit=3, seksi='3C'))
    #  print()

    #  print(statPegawaiByTask(df_task_pegawai, 'pelaksana11C5'))
    #  print()

    #  print(statTaskByNumPegawai(df_task_pegawai, task=None))
    #  print()

    #  print(statTaskByNumPegawai(df_task_pegawai, task='Task-27'))
    #  print()

    #  print(getUnitList(df_pegawai, level='seksi', upperUnit=1))
    #  net = Network(height='500px', width="100%", bgcolor='#FFFFFF', font_color='black')
    #  print(graphOverviewTIK(df_pegawai, df_task_pegawai, net=net))

    #  print(getPegawaiList(df_pegawai))
    #  print()

    #  print(getPegawaiList(df_pegawai, subdit=1, seksi="all"))
    #  print()

    #  merge_ = pd.merge(df_pegawai[(df_pegawai["subdit"] == 3) & (df_pegawai["seksi"] == "3C")], 
    #                    df_task_pegawai, on="idpegawai", how="left").groupby(['idpegawai','jenistask']).agg('count').reset_index()[['idpegawai','jenistask','task']]
    #  print(merge_)
    #  print(df_pegawai[(df_pegawai["subdit"] == 3) & (df_pegawai["seksi"] == "3C")])
    #  print()
    #  print(pd.merge(df_pegawai[(df_pegawai["subdit"] == 3) & (df_pegawai["seksi"] == "3C")], 
    #                    df_task_pegawai, on="idpegawai", how="left").groupby(['idpegawai','jenistask']).agg('count'))
     
    #  merge_ = list(pd.merge(df_pegawai[(df_pegawai['subdit'] == 1) & (df_pegawai['jabatan'] != 'kasi')], 
    #                 df_task_pegawai, on="idpegawai", how="left")[['idpegawai','namapegawai','task']].apply(
    #                     lambda x: [f"{x['namapegawai']} ({x['idpegawai']})", x['task']]
    #                 ,axis=1))
    #  print(merge_)
    #  print()
    #  print(list(set([m[0] for m in merge_])))
    #  print()
    #  print(list(set([m[1] for m in merge_ if str(m[1]) != 'nan'])))
     
    #  print(statTaskByPegawai(df_pegawai, df_task_pegawai, 2, '2B', idpegawai=['Iliya (pelaksana22B4)']))

    #  print(getAllTasks(df_pegawai, df_task_pegawai))