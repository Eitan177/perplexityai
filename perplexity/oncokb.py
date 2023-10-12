import streamlit as st
import pandas as pd
import numpy as np
import re
import json
import requests
from io import StringIO
from perplexity import Perplexity
import codecs



st.set_page_config(layout="wide")
def dataread(kk, pasteduse,perplex_use):

    if pasteduse != '':
        data = pd.read_csv(StringIO(pasteduse),sep='\t',header=0)
        data['Gene']=data['Gene_name']
        data['Protein Change']=data['Protein Change'].apply(lambda x: str(x).replace('p.',''))

    st.write('The data you input is the following:')
    st.write(data)

    all_onc=[]
    all_perplex=[]
    all_query=[]
    querygeneprotein=[]
    for index,row in data.iterrows():
       
        if str(row['Gene']) != 'nan' and str(row['Protein Change']) != 'nan':
            
            if str(row['Protein Change']) != 'nan':
                d1=requests.get("https://www.oncokb.org/api/v1/annotate/mutations/byProteinChange?hugoSymbol="+row['Gene']+"&alteration="+row['Protein Change']+"&tumorType="+kk, headers={'Accept': 'application/json',"Authorization": 'Bearer 64f4aa64-2509-4500-994b-1f2a38422d44'})
                if perplex_use:
                    query="what drugs are used to treat "+ row['Gene']+" "+row['Protein Change']+" in "+kk+"?"
                    perplexity = Perplexity()   
                    answer=perplexity.search(query)
                    all_perplex.append(answer)
                    all_query.append(query)
                all_onc.append(d1.content)
                
                querygeneprotein.append(row['Gene']+"&alteration="+row['Protein Change'])
                #if perplex_use:
                #    perplexity.close()

    return all_onc,all_perplex,all_query,querygeneprotein


with st.form(key='parameters'):


    texttomatch=st.text_input('text to match',value='')
    pasteduse=st.text_area('paste text to search',value='')
    perplex_use=st.checkbox('Use Perplexity',value=False)
    abbrev_perplex=st.checkbox('Abbreviate Perplexity',value=True)
    submit_button = st.form_submit_button(label='Submit')
if submit_button:

    if pasteduse != '':
        kk,perplexity, query,querygeneprotein=dataread(texttomatch,pasteduse,perplex_use)
        dictionary_of_json_fda={}
        dictionary_of_json_text={}
        dictionary_of_json_text_perplexity={}
        dictionary_of_json_query={}
        dictionary_of_drugs={}
        for i in np.arange(0,len(kk)):
            output = codecs.decode(kk[i])
            dictionary_of_json_fda[querygeneprotein[i]]=json.loads(output).get('highestFdaLevel')
            #dictionary_of_drugs[querygeneprotein[i]]=json.loads(output).get('treatments').get('drugs').get('DrugName')
            dictionary_of_json_text[querygeneprotein[i]]=json.loads(output)
            dictionary_of_json_text_perplexity[querygeneprotein[i]]=perplexity[i]
            dictionary_of_json_query[querygeneprotein[i]]=query[i]
        ord_dict=sorted(dictionary_of_json_fda.items(), key=lambda item: str(item[1]))
        
        tt=st.tabs(pd.DataFrame(ord_dict).apply(lambda n: str(n[0])+' '+str(n[1]),axis=1).to_list())
        counter=0
       
        for i in ord_dict:
            with tt[counter]:
                st.write('The query was '+i[0])
                st.write('The results were:')   
                if dictionary_of_json_text[i[0]]['highestFdaLevel'] != '':
                    st.write('Drugs in this result')
                    drugnames=[]
                    for d in dictionary_of_json_text[i[0]]['treatments']:
                        for dd in d['drugs']:
                            drugnames.append(dd['drugName'])
                    for m in (set(drugnames)):
                        st.write(m)
                    st.write(str(len(set(drugnames)))+' drugs in this result')
                if perplex_use:
                    st.write('The perplexity query was '+dictionary_of_json_query[i[0]])
                    
                    
                    for jj in dictionary_of_json_text_perplexity[i[0]]:   
                        forout=jj
                    st.write('answer from perplexity')              
                    st.write(forout["answer"])
                    for m in (set(drugnames)):
                        if(re.findall(m,forout["answer"])) !=[]:
                            st.write('YES BOTH '+m+' is in the answer of perplexity')
                        else:
                            st.write('NO JUST ONCOKB '+m+' is not in the answer of perplexity')    
                st.write('all oncokb results')            
                st.json(dictionary_of_json_text[i[0]])  
                if perplex_use and abbrev_perplex ==False:  
                    st.write('All results from perplexity:')
                    st.write(forout)
                    #breakpoint()    
                counter=counter+1
