#!/usr/bin/env python
# coding: utf-8

# # Analisi del processo di acquisizione cliente

# Questo notebook contiene le analisi riguardanti il processo di acquisizione dei clienti tramite l'app Gimme 5.
# 
# Gli obiettivi dell'analisi sono:
#  * Descrivere il processo attuale
#  * Evidenziare eventuali opportunità per migliorare il processo al fine di aumentare la conversion rate

# ### Definizioni preliminari

# Import necessari all'analisi.

# In[1]:


conda install -c conda-forge plotnine


# In[2]:


import pandas as pd
from datetime import datetime


get_ipython().run_line_magic('matplotlib', 'inline')


# La funzione **processFunnelData** prende in ingresso un dataframe e calcola le statistiche necessarie per valutare la progressione nel funnel. I calcoli effettuati sono brevemente descritti nei commenti e più in dettaglio in sezioni successive del notebook.

# In[3]:


def processFunnelData(df):
    # il dataframe df deve essere strutturato in modo che
    # * ogni riga rappresenti uno step del funnel (id numerico nella colonna stage e descrizione nella colonna Stato_Utente)
    # * le colonne si dividono in:
    #   - colonne indice che contengono variabili descrittive (es. Stato_Utente)
    #   - colonne che rappresentano variabili in base a cui sezionare l'analisi del funnel (es. anno di sottoscrizione, importo bonus, ...)
    
    funnelData = df.copy()
    
    # definizione delle colonne indice che vengono escluse dall'analisi
    indexCols = ["Registration_Step","Registration_SubStep","Description_Registration_Step","User_Status_Detail"]
    varCols = [x for x in df.columns.tolist() if x not in indexCols]
    
    # per ogni variabile su cui valutare la progressine nel funnel vengono calcolate diverse statistiche
    # (si ricordi che ogni riga rappresenta uno stato del funnel) 
    for col in varCols:
        funnelData.sort_values(by="stage", ascending=False, inplace=True)
        
        # *col*_funnelProgression contiene l'avanzamento progressivo nel funnel. Per ogni riga, questa
        # statistica indica quante leads hanno completato il relativo step del processo di registrazione
        # o uno step successivo.
        funnelData["{}_funnelProgression".format(col)] = funnelData[col].cumsum()
        funnelData.sort_values(by="stage", ascending=True, inplace=True)
        
        # *col*_startingFrom è una variabile di supporto che indica quante leads hanno completato
        # lo step precedente
        funnelData["{}_startingFrom".format(col)] = funnelData["{}_funnelProgression".format(col)].shift()
        
        # *col*_stageLoss indica quante leads sono arrivate allo stage relativo alla riga,
        # ma non lo hanno completato
        funnelData["{}_stageLoss".format(col)] = funnelData["{}_funnelProgression".format(col)].diff()
        
        # *col*_keptStage indica la completion rate del singolo stage del funnel. Il valore in questa
        # colonna è la percentuale di leads che hanno completato lo step fatte 100 le lead che sono 
        # arrivate allo step. Es: un valore di 0.50 indica che su 100 leads arrivate allo step X, solo 50
        # lo hanno completato.
        funnelData["{}_keptStage".format(col)] = funnelData["{}_funnelProgression".format(col)]/funnelData["{}_startingFrom".format(col)]
        
        # *col*_keptOverll traccia in temini percentuali la progressione nel funnel. Il valore in questa
        # colonna è la percentuale di leads che hanno completato lo step fatte 100 le lead che hanno 
        # iniziato il processo di sottoscrizione. Es: un valore di 0.50 indica che su 100 leads che hanno
        # iniziato il processo di sottoscrizione, solo 50 sono arrivte a completare lo step X.
        funnelData["{}_keptOverall".format(col)]  = funnelData["{}_funnelProgression".format(col)]/funnelData["{}_funnelProgression".format(col)].max()
        
    return funnelData


# ## Caricamento dei dati e preprocessing

# I dati vengono caricati e, dove necessario, le colonne vengono convertite nei formati opportuni (es. _datetime_).

# In[4]:


a2users = pd.read_csv(r'C:\Users\elisa\Downloads\a2usersOK.csv',sep=';',low_memory=False)


# In[5]:


a2users.head(10) #sex is 1 or 2 (anonymized this too)


# In[6]:


exclude = a2users["Last_Online_Subscription"] == "AcomeA" #get rid of those customers coming from AcomeA NOT Gimme5
a2users = a2users[~exclude].copy() #~operator get the complementary

a2users["DateTime_Subscription"] = pd.to_datetime(a2users["DateTime_Subscription"]) #make the date in time format


# In[7]:


a2users


# In[8]:


a2users.columns


# Per le analisi vengono considerate solo le leads generate attraverso il processo di sottoscrizione corrente (ovvero create dopo il 01/10/2017.

# In[9]:


subset = a2users["DateTime_Subscription"].apply(lambda x: x>datetime(2017,10,1))
a2users = a2users[subset].copy()
del subset #get rid of all the info about subscriptions before that time


# In[10]:


#subset2 = a2users["DateTime_Subscription"].apply(lambda x: x>datetime(2019,10,1))
#this can be used if we want to merge info in the subscription table and the funnel table
#since users in the subscription table are considered from Oct 2019


# Esplorazione prelinimare (colonne disponibili, analisi stato utente ed età).

# In[11]:


a2users.columns


# In[12]:


a2users["User_Status_Detail"].value_counts() #for each status check they are not the same and also get rid of 
#the 'Solo su AcomeA-Online' since we already filter by AcomeA before.
#User Test is NOISE: eliminated
#User canceled gives instead info: they canceled before termining the subscription process.
#Here we are performing another kind of analysis and we get rid also of Canceled User but it actually is informative


# In[13]:


a2users["ageBand"].value_counts()


# L'anno di sottoscrizione (colonna _subscr_year_) viene inizializzato a 0 per i casi in cui risulta mancante (_NaN_) e convertito a int.

# In[14]:


a2users.loc[pd.isna(a2users["subscr_year"]),"subscr_year"] = 0             #subscript. year = 0 must be canceled
a2users["subscr_year"] = a2users["subscr_year"].astype(int)         #set to integers these years


# Viene definita la variabile _stage_ - variabile numerica che descrive la progressione nel funnel come definito da _Stato_Utente_ in modo descrittivo.
# Vengono scartati
# * gli utenti che hanno come stato "A - Solo su AcomeA-online" - ovvero utenti non Gimme5
# * gli utenti che non hanno uno stato utente valido ( _stage_ == -1)

# In[15]:


# move into make_dataset.py or into the data extraction queries
a2users = a2users[a2users["User_Status_Detail"]!="A - Solo su AcomeA-Online"].copy()

a2users["stage"] = -1 
#users are classified in stage = -1 by default, but if they have User_Status_Detail as follow they are reclassified

a2users.loc[a2users["User_Status_Detail"]=="0 - E-Mail non verificata","stage"] = 0 
#set =0 the values of the User_Status_Detail col equal to "0 - E-Mail non verificata" and add column "stage"
a2users.loc[a2users["User_Status_Detail"]=="1 - Mail Validata","stage"] = 1
a2users.loc[a2users["User_Status_Detail"]=="2 - Sottoscrizione Iniziata","stage"] = 2
a2users.loc[a2users["User_Status_Detail"]=="3 - Codice Fiscale OK","stage"] = 3
a2users.loc[a2users["User_Status_Detail"]=="4 - Dati Personali OK","stage"] = 4
a2users.loc[a2users["User_Status_Detail"]=="5 - Residenza OK","stage"] = 5
a2users.loc[a2users["User_Status_Detail"]=="6 - Documento ID OK","stage"] = 6
a2users.loc[a2users["User_Status_Detail"]=="7 - Documenti Firmati","stage"] = 7
a2users.loc[a2users["User_Status_Detail"]=="8 - Antiriciclaggio OK","stage"] = 8
a2users.loc[a2users["User_Status_Detail"]=="9 - Fondo Scelto","stage"] = 9
a2users.loc[a2users["User_Status_Detail"]=="10 - Concluso","stage"] = 10

a2users = a2users[a2users["stage"]>-1].copy() #we get rid of those that are stacked at stage, but actually we already done this by
# get rid of the User test and Canceled User


# In[16]:


a2users.head()


# Viene creata una variabile che descrive il tipo di login effettuato dall'utente (_inf_loginType_).
# I valori possono essere: _Facebook_, _Google_, _Multi_ (l'utente ha utilizzato sia _Facebook_ che _Google_), _Altri_ (l'utente ha effettuato il login creando un utente tramite indirizzo email).

# In[17]:


a2users["has_ID_GPlus"]==0


# In[18]:


a2users["inf_loginType"] = "Altri" #create also another column called "inf_loginType" and set its default value equal to "Altri"

#Then those who have these characteristics will change the default value for column "inf_loginType"
fb = (a2users["has_ID_Facebook"]==1) & (a2users["has_ID_GPlus"]==0)
a2users.loc[fb,"inf_loginType"] = "Facebook"

gp = (a2users["has_ID_Facebook"]==0) & (a2users["has_ID_GPlus"]==1)
a2users.loc[gp,"inf_loginType"] = "Google"

multi = (a2users["has_ID_Facebook"]==1) & (a2users["has_ID_GPlus"]==1)
a2users.loc[multi,"inf_loginType"] = "Multi"


# In[19]:


a2users["inf_loginType"].value_counts()


# ## Inizio analisi del processo di sottoscrizione

# Il dataframe che contiene i dati utente viene riaggregato per poter analizare la progressione nel funnel nei diversi anni.

# In[20]:


funnelDataY = a2users.groupby(["stage","User_Status_Detail","subscr_year"])["ID_User"].count().reset_index()
#group by these columns and count the userid for each
funnelDataY
#so for each stage and aech of the three considered years we count the user_id in order to see the funnel


# Il dataframe _funnelData_ viene riorganizzato in formato "tabulare": ogni riga rappresenta un passo specifico del processo di sottoscrizione, le colonne rappresentano i diversi anni. Il valore di ogni cella (riga _s_ - colonna _y_) rappresenta il numero di leads create in un anno (_y_) e attualmente ferme in uno stato (_s_).

# In[21]:


funnelStageYear = pd.pivot_table(funnelDataY, index=["stage","User_Status_Detail"],columns="subscr_year",values="ID_User")
#we alsp run a pivot to understand


# In[22]:


funnelStageYear #how many user ids are stacked for each step in each year
# gimme5 spent a lot of budget in get them know to a lot of people, but there are too many email non verificata that means a 
# totally loose of budget


# Il dataframe in formato tabulare (_funnelStageYear_) viene processato per calcolare le statistiche necessarie per valutare la progressione attraverso il funnel delle leads - sezionando l'analisi per anno di sottoscrizione.
# Le variabili descritte nella definizione della funzione **processFunnelData** sono calcolate e restituite in output per ogni anno.
# In altre parole, il dataset conterrà le colonne:
# * \*anno\*_funnelProgression
# * \*anno\*_startingFrom
# * \*anno\*_stageLoss
# * \*anno\*_keptStage
# * \*anno\*_keptOverall
# 
# per ogni \*anno\* contenuto nel dataframe (attualmente 2017, 2018, 2019).

# In[23]:


funnelProgrSY = processFunnelData(funnelStageYear.reset_index())
#cols = ["User_Status_Detail",2017,2018,2019,"2017_keptOverall","2018_keptOverall","2019_keptOverall"] #normalized to 1 values
cols = ["User_Status_Detail",2017,2018,2019,"2017_keptStage","2018_keptStage","2019_keptStage"]
funnelProgrSY[cols]


# we can see that in 2017 about an half of the validated mail 
# Note that after setting the fiscal code, people go through the process: the 90% of those inserting the fiscal code then insert also the personal data

# In[24]:


funnelProgrSY = processFunnelData(funnelStageYear.reset_index())
#cols = ["User_Status_Detail",2017,2018,2019,"2017_keptOverall","2018_keptOverall","2019_keptOverall"]
cols = ["User_Status_Detail",2017,2018,2019,"2017_keptStage","2018_keptStage","2019_keptStage"]
funnelProgrSY[cols]


# It is the same table but a funnel visualizations, how many clients are left at each step?

# Il dataframe viene riorganizzato per poter essere visualizzato tramite plotnine (clone Python di ggplot2).

# In[25]:


categories = funnelProgrSY["User_Status_Detail"].values
dfSY = pd.melt(funnelProgrSY[["User_Status_Detail","2017_keptOverall","2018_keptOverall","2019_keptOverall"]], id_vars="User_Status_Detail")


# In[26]:


from plotnine import ggplot, geom_col, scale_x_discrete, coord_flip, facet_wrap, aes


# In[27]:


( ggplot(dfSY)
 + geom_col(aes(x="User_Status_Detail", y="value"))
 + scale_x_discrete(limits=categories[::-1])
 + coord_flip()
 + facet_wrap("subscr_year")
)


# Analisi del funnel ripetuta sezionando per tipo di login. 

# In[28]:


funnelDataLog = a2users.groupby(["stage","User_Status_Detail","inf_loginType"])["ID_User"].count().reset_index()
funnelStageLog = pd.pivot_table(funnelDataLog, index=["stage","User_Status_Detail"],columns="inf_loginType",values="ID_User",fill_value=0)

funnelProgrSL = processFunnelData(funnelStageLog.reset_index())
funnelProgrSL[["User_Status_Detail","Altri","Facebook","Google","Multi","Altri_keptOverall","Facebook_keptOverall","Google_keptOverall","Multi_keptOverall"]]


# ## Analisi 2019

# In questa sezione vengono presentate analisi di funnel per il solo 2019. Le analisi per altri anni possono essere ottenute modificando la variabile *tgt_year* nelle diverse celle.

# Analisi del funnel sezionata per importo del bonus di onboarding. (in 2019 )

# In[29]:


tgt_year = 2019

importoNA = pd.isna(a2users["Subscription_Bonus"])
a2users.loc[importoNA,"Subscription_Bonus"] = 0 #set equal to 0 the Subscription_Bonus that has null value

# modificando le seguenti condizioni è possibile filtrare gli utenti
# in base al tipo di promozione (MGM o normale) ##MGM= member_get_member promo
subset = (a2users["subscr_year"]==tgt_year) #& (a2users["stage"] > 2) #& (a2users["Tipo_Hidden-Link"] == "Link Codice Promo Attivo")
#subset = (a2users["subscr_year"]==tgt_year) & (a2users["Tipo_Hidden-Link"] == "MGM")

funnelDataBonus = a2users[subset].groupby(["stage","User_Status_Detail","Subscription_Bonus"])["ID_User"].count().reset_index()
del subset

funnelStageBonus = pd.pivot_table(funnelDataBonus, index=["stage","User_Status_Detail"],columns="Subscription_Bonus",values="ID_User",fill_value=0)

funnelProgrSB = processFunnelData(funnelStageBonus.reset_index())

# diverse opzioni per definire le colonne da visualizzare
#cols = ["Stato_Utente"] + [x for x in ff.columns if "_keptOverall" in str(x)]
#cols = ["Stato_Utente",'0.0_funnelProgression',"5.0_funnelProgression", "10.0_funnelProgression", "15.0_funnelProgression","0.0_keptOverall","5.0_keptOverall","10.0_keptOverall","15.0_keptOverall"]
#cols = ["User_Status_Detail","0.0_keptStage","5.0_keptStage","10.0_keptStage","15.0_keptStage"]
#cols = ["Stato_Utente","0.0_keptStage","5.0_keptStage","10.0_keptStage"]
cols = ["User_Status_Detail","0.0_keptOverall","5.0_keptOverall","10.0_keptOverall","15.0_keptOverall"]
#cols = ["Stato_Utente","5.0_funnelProgression", "10.0_funnelProgression", "15.0_funnelProgression","5.0_keptOverall","10.0_keptOverall","15.0_keptOverall"]

funnelProgrSB[cols]
#when you give 5 euros, 10 or 15euros bonus you have more prob to complete subscription than times you don't give abonus 0.0_keptOverall


# In[30]:


a2users


# In[31]:


users10= a2users[a2users['Subscription_Bonus']== 10.0]


# In[32]:


users15= a2users[a2users['Subscription_Bonus']== 15.0]


# In[33]:


users5= a2users[a2users['Subscription_Bonus']== 5.0]


# In[34]:


import numpy as np


# In[35]:


users10


# In[36]:


print(users10.shape)
print(users15.shape)
print(users5.shape)


# In[37]:


a2users['Subscription_Bonus'].value_counts()


# ### Some analysis on those having received the 10.0 euros bonus

# In[38]:


subset = (a2users["subscr_year"]==tgt_year)
users10= users10[subset]


# In[39]:


users10['ID_Promotion'].value_counts()


# In[40]:


import matplotlib.pyplot as plt
plt.hist(users10['ID_Promotion'], bins = range(0,40,1))


# In[41]:


users10['ageBand'].value_counts()


# In[42]:


users10['ageBand'].value_counts()/users10.shape[0]


# In[43]:


users10['inf_loginType'].value_counts()/users10.shape[0]   #those receiving the 10euros bonus split by login type


# In[44]:


funnelusers10Bonus = users10[subset].groupby(["stage","User_Status_Detail","Subscription_Bonus"])["ID_User"].count().reset_index()


# In[45]:


funnelStageBonus10 = pd.pivot_table(funnelusers10Bonus, index=["stage","User_Status_Detail"],columns="Subscription_Bonus",values="ID_User",fill_value=0)

funnelProgrSB10 = processFunnelData(funnelStageBonus10.reset_index())


# In[46]:


cols10= ['stage','User_Status_Detail','stage_keptOverall','10.0_keptOverall']
funnelProgrSB10[cols10]


# In[47]:


#for those having subscribed in 2019 with a 10.0euros bonus and arrived at the conclusion of the subscription process,
#how long after the subscription did they make the first investment?
a2users.columns #take DateTime_Subscription and DateTime_First_Investment


# In[48]:


concluded10 = users10[users10['stage']==10]
concluded10


# In[49]:


plt.hist(concluded10['ID_Promotion'])


# In[50]:


invNA = pd.isna(a2users['DateTime_First_Investment'])
a2users.loc[invNA,'DateTime_First_Investment'] = 0
a2users[a2users['DateTime_First_Investment']!= 0]['DateTime_First_Investment'] #in the whole db we have 9079 customers having already invested
#we want to see the same thing in those having received a 10 bonus in 2019 and having completed subscription


# In[51]:


invNA = pd.isna(concluded10['DateTime_First_Investment'])
concluded10.loc[invNA,'DateTime_First_Investment'] = 0
concluded10[concluded10['DateTime_First_Investment']!= 0]['DateTime_First_Investment'] #there are 194 people having already invested
#let's call them inv10


# In[52]:


inv10 = concluded10[concluded10['DateTime_First_Investment']!= 0]


# In[53]:


inv10.shape[0] / concluded10.shape[0] #only the 10% actually invested


# In[67]:


#inv10['DateTime_First_Investment']
inv10['DateTime_Subscription']


# In[94]:


inv10['NEWDateTime_First_Investment'] = inv10['DateTime_First_Investment'].dt.strftime('%d/%m/%Y')
inv10['NEWDateTime_First_Investment'] = pd.to_datetime(inv10['NEWDateTime_First_Investment'])

inv10['NEWDateTime_Subscription'] = inv10['DateTime_Subscription'].dt.strftime('%d/%m/%Y')
inv10['NEWDateTime_Subscription'] = pd.to_datetime(inv10['NEWDateTime_Subscription'])


# In[95]:


inv10


# In[96]:


inv10['afterwhen10'] = (inv10['NEWDateTime_First_Investment']- inv10['NEWDateTime_Subscription'])


# In[97]:


inv10[['ID_User', 'DateTime_Subscription', 'DateTime_First_Investment', 'afterwhen10']]


# In[98]:


type(inv10['afterwhen10'])


# In[99]:


print(inv10['afterwhen10'].mean())
print(inv10['afterwhen10'].max())
print(inv10['afterwhen10'].min())


# ### Some analysis on those having received the 15.0 euros bonus

# In[143]:


users15 = users15[subset]


# In[145]:


users15['ID_Promotion'].value_counts() #for 15 euros bonus the codes were 23 


# In[146]:


users15['inf_loginType'].value_counts()/users15.shape[0]  #they mostly subscribed through other ways than FB or Google


# In[147]:


users15['ageBand'].value_counts()  #the segment using this code is in the 25-30 yo stage


# In[148]:


users15.shape


# In[149]:


users15['ageBand'].value_counts()/users15.shape[0]   #Since the age is available only after the 2nd step, once included the
                                                     #fiscal code, from Na we see that small % of those having received the 
                                                     #15.0 bonus quit before giving the fiscal code


# In[150]:


funnelusers15Bonus = users15[subset].groupby(["stage","User_Status_Detail","Subscription_Bonus"])["ID_User"].count().reset_index()


# In[151]:


funnelStageBonus15 = pd.pivot_table(funnelusers15Bonus, index=["stage","User_Status_Detail"],columns="Subscription_Bonus",values="ID_User",fill_value=0)

funnelProgrSB15 = processFunnelData(funnelStageBonus15.reset_index())
cols15 = ['stage','User_Status_Detail','stage_keptOverall','15.0_keptOverall']
funnelProgrSB15[cols15]


# In[100]:


concluded15 = users15[users15['stage']==10]
concluded15


# In[101]:


plt.hist(concluded15['ID_Promotion'])


# In[102]:


inv15NA = pd.isna(concluded15['DateTime_First_Investment'])
concluded15.loc[inv15NA,'DateTime_First_Investment'] = 0
concluded15[concluded15['DateTime_First_Investment']!= 0]['DateTime_First_Investment'] #there are 194 people having already invested
#let's call them inv15


# In[103]:


inv15 = concluded15[concluded15['DateTime_First_Investment']!= 0]


# In[104]:


inv15.shape[0]/concluded15.shape[0] #same % as before: only the 10% actually invests even if they subscribe


# In[128]:


inv15['NEWDateTime_First_Investment'] = pd.to_datetime(inv15['DateTime_First_Investment'])
inv15['NEWDateTime_Subscription'] = pd.to_datetime(inv15['DateTime_Subscription'])


# In[129]:


inv15[['DateTime_Subscription', 'DateTime_First_Investment','NEWDateTime_Subscription', 'NEWDateTime_First_Investment']]


# In[130]:


inv15['NEWDateTime_Subscription'] = pd.to_datetime(inv15['NEWDateTime_Subscription'])
inv15['NEWDateTime_First_Investment'] = pd.to_datetime(inv15['NEWDateTime_First_Investment'])


# In[131]:


type(inv15['NEWDateTime_Subscription'])


# In[132]:


type(inv15['NEWDateTime_First_Investment'])


# In[134]:


inv15['NEWDateTime_First_Investment'] = inv15['NEWDateTime_First_Investment'].dt.strftime('%d/%m/%Y')
inv15['NEWDateTime_Subscription'] = inv15['NEWDateTime_Subscription'].dt.strftime('%d/%m/%Y')


# In[136]:


inv15['NEWDateTime_First_Investment'] = pd.to_datetime(inv15['NEWDateTime_First_Investment'])

inv15['NEWDateTime_Subscription'] = pd.to_datetime(inv15['NEWDateTime_Subscription'])


# In[137]:


inv15['afterwhen15'] = (inv15['NEWDateTime_First_Investment']- inv15['NEWDateTime_Subscription'])


# In[138]:


inv15 #we can see that the two ones having received the 15 euros bonus invested after few days


# ### Some analysis on those having received the 5.0 euros bonus

# In[152]:


users5= users5[subset]


# In[153]:


users5['ID_Promotion'].value_counts() #35 is the code for the MGM promotion


# In[154]:


plt.hist(users5['ID_Promotion'], bins = range(0,40))


# In[155]:


users5['inf_loginType'].value_counts()/users5.shape[0]  #also in this case the way they start subscription process is mainly different from FB or Google


# In[156]:


users5['ageBand'].value_counts()


# In[157]:


users5['ageBand'].value_counts()/users5.shape[0] #in this case there is a high percentage of people lost when asking fiscal code


# In[158]:


funnelusers5Bonus = users5[subset].groupby(["stage","User_Status_Detail","Subscription_Bonus"])["ID_User"].count().reset_index()


# In[159]:


funnelStageBonus5 = pd.pivot_table(funnelusers5Bonus, index=["stage","User_Status_Detail"],columns="Subscription_Bonus",values="ID_User",fill_value=0)

funnelProgrSB5 = processFunnelData(funnelStageBonus5.reset_index())
cols5 = ['stage','User_Status_Detail','stage_keptOverall','5.0_keptOverall']
funnelProgrSB5[cols5]


# In[160]:


#is there a variable indicating where did they hear about Gimme5 for the first time?
#to understand which marketing channel is performing better for this product and if there are any differences in the completed
#subscription steps for customers coming from different marketing channels


# In[139]:


concluded5 = users5[users5['stage']==10]
concluded5


# In[140]:


plt.hist(concluded5['ID_Promotion'])


# In[141]:


inv5NA = pd.isna(concluded5['DateTime_First_Investment'])
concluded5.loc[inv5NA,'DateTime_First_Investment'] = 0
concluded5[concluded5['DateTime_First_Investment']!= 0]['DateTime_First_Investment'] #there are 194 people having already invested
#let's call them inv5


# In[143]:


inv5 = concluded5[concluded5['DateTime_First_Investment']!= 0]
inv5


# In[144]:


inv5.shape[0]/concluded5.shape[0] # only the 15% actually invests even if they subscribe


# In[145]:


inv5['NEWDateTime_First_Investment'] = pd.to_datetime(inv5['DateTime_First_Investment'])
inv5['NEWDateTime_Subscription'] = pd.to_datetime(inv5['DateTime_Subscription'])


# In[147]:


inv5[['DateTime_Subscription', 'DateTime_First_Investment','NEWDateTime_Subscription', 'NEWDateTime_First_Investment']]


# In[153]:


inv5['NEWDateTime_Subscription'] = pd.to_datetime(inv5['NEWDateTime_Subscription'])
inv5['NEWDateTime_First_Investment'] = pd.to_datetime(inv5['NEWDateTime_First_Investment'])


# In[154]:


inv5['NEWDateTime_First_Investment'] = inv5['NEWDateTime_First_Investment'].dt.strftime('%d/%m/%Y')
inv5['NEWDateTime_Subscription'] = inv5['NEWDateTime_Subscription'].dt.strftime('%d/%m/%Y')


# In[155]:


inv5['NEWDateTime_First_Investment'] = pd.to_datetime(inv5['NEWDateTime_First_Investment'])
inv5['NEWDateTime_Subscription'] = pd.to_datetime(inv5['NEWDateTime_Subscription'])


# In[158]:


inv5['afterwhen5'] = (inv5['NEWDateTime_First_Investment']- inv5['NEWDateTime_Subscription'])
inv5['afterwhen5']


# In[160]:


print(inv5['afterwhen5'].mean())
print(inv5['afterwhen5'].max())
print(inv5['afterwhen5'].min()) #we can see that in mean they spend more time from the subscription to the first investment, sometimes also 2 years!


# Remember that 15euros bonus is given to very few people!
# Seems people is sensitive to have or not a bonus but not to the amount of the bonus

# ### Analisi del funnel sezionata per tipo di login (ripetuta utilizzando solo i dati 2019).

# In[59]:


tgt_year = 2019

funnelDataLog_y = a2users[a2users["subscr_year"]==tgt_year].groupby(["stage","User_Status_Detail","inf_loginType"])["ID_User"].count().reset_index()
funnelStageLog_y = pd.pivot_table(funnelDataLog_y, index=["stage","User_Status_Detail"],columns="inf_loginType",values="ID_User",fill_value=0)

funnelProgrSL_y = processFunnelData(funnelStageLog_y.reset_index())
funnelProgrSL_y[["User_Status_Detail","Altri","Facebook","Google","Multi","Altri_keptOverall","Facebook_keptOverall","Google_keptOverall","Multi_keptOverall"]]


# Analisi del funnel sezionata per età delle leads.
# 
# **ATTENZIONE**: l'età è calcolabile/disponibile solo **dopo** che la lead ha registrato il codice fiscale. Per questo motivo l'analisi non include gli stati precedenti.

# In[53]:


tgt_year = 2019

subset = (a2users["subscr_year"]==tgt_year) & (a2users["stage"]>2)
funnelDataAge = a2users[subset].groupby(["stage","User_Status_Detail","ageBand"])["ID_User"].count().reset_index()
del subset

funnelStageAge = pd.pivot_table(funnelDataAge, index=["stage","User_Status_Detail"],columns="ageBand",values="ID_User",fill_value=0)

funnelProgrSA = processFunnelData(funnelStageAge.reset_index())


# Confronto delle statistiche della completion rate per ogni stage del funnel per fasce di età. La statistica scelta è la completion rate che è più semplicemente confrontabile con l'analisi aggregata (senza divisione per età). Per utilizzare le altre statistiche, si ricordi che in questa fase si sta considerando come step 0 l'inserimento del codice fiscale (dato che prima di quel momento non è possibile determinare l'età della lead).

# In[54]:


# ATTENZIONE: se si decide di utilizzare _keptOverall come statistica
# si ricordi che la baseline (100%) non è più il numero di leads create
# ma il numero di leads che hanno inserito il codice fiscale. Questo rende
# la statistica non confrontabile con le analisi precedenti.
#cols = ["Stato_Utente"] + [x for x in funnelProgrSA.columns if "_keptOverall" in x]
cols = ["User_Status_Detail"] + [x for x in funnelProgrSA.columns if "_keptStage" in x]
funnelProgrSA[cols]


# Visulizzazione di tutte le statistiche di progressione nel funnel per una singola fascia di età.

# In[59]:


ageBands = ["18-20","20-25","25-30","30-35","35-40","40-45","45-50","50-55","55-60","60-65","65+"]

ageBand = ageBands[1]
cols = ["User_Status_Detail"] + [x for x in funnelProgrSA.columns if ageBand in x]

funnelProgrSA[cols]


# In[ ]:




