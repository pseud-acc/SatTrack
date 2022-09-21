#!/usr/bin/env python

"""

This module scrapes data from the skyrocket website and enriches satellite launch vehicle class and use type data in the existing satellite catalogue.

Example:

        $ python skyrocket_webscraper.py

Attributes:
    module_level_variable1 (int): 

Todo:
    * Export column distributions to csv/plots 

"""

import re # standard library

import pandas as pd # 3rd party packages
import numpy as np
import requests
from bs4 import BeautifulSoup 
import unidecode
from dateutil import parser
from datetime import datetime
import time
import sqlite3

import string
import nltk

def skyrocket_update_check(metadata_location, full_check):
    ''' 
    Check whether Skyrocket webscraped data needs updating.
    
    @param full_check: (boolean) If true, check sub-webpages
    @param metadata_location: (str) filename of Skyrocket download metadata
    '''
    
    # Create list of skyrocket webpages in satellite directory
    url_home = "https://space.skyrocket.de/"
    url_dir = url_home + "directories/"
    url_sat = url_dir + "sat.htm"

    ##Initialise list to store last update dates for each url
    urls_lu = []
    # Check last update date
    html = requests.get(url = url_sat).text
    soup = BeautifulSoup(html, "html.parser")
    tags_lu = soup.find_all("div", class_ ="footerdate")
    urls_lu.append(re.findall("Last update:(.*)",tags_lu[0].contents[0])[0].strip() )
    # Extract skyrocket webpages for all countries
    if full_check:
        ##Create list of html tags for satellite application-country webpages
        tags = soup.find_all("ul", class_="country-list mcol2")
        for t in tags:
            for a in t.findAll("a"):
                # Check last update date
                html_lu = requests.get(url = url_dir + a["href"]).text
                soup_lu = BeautifulSoup(html_lu, "html.parser")
                tags_lu = soup_lu.find_all("div", class_ ="footerdate")
                urls_lu.append(re.findall("Last update:(.*)",tags_lu[0].contents[0])[0].strip())
            
    # Extract most recent update date
    last_update = max([parser.parse(a, dayfirst=True) for a in urls_lu])
    last_update_str = last_update.strftime("%d/%m/%Y, %H:%M:%S")
    
    # Check download metadata
    filename = metadata_location
    metadata = pd.read_csv(filename)
    metadata_last_download = metadata[metadata["Source"] == "Skyrocket"]["Last Download"].values[0]
    print("Last Skyrocket download: ",  metadata_last_download)
    if parser.parse(metadata_last_download, dayfirst=True) < last_update:
        today = datetime.now()
        metadata.loc[metadata["Source"] == "Skyrocket","Last Download"] = today.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.loc[metadata["Source"] == "Skyrocket","Last Update"] = last_update.strftime("%d/%m/%Y, %H:%M:%S")
        metadata.to_csv(filename, index=False)
        return True, last_update_str        
    else:
        return False, last_update_str  

    
def webscraper_dump(dbs_name):

    ''' 
    Import merged satellite catalogue data from SQL database and extract satellites with missing data

    @param dbs_name: (str) name of sqlite database to write in merged satallite catalogue data
    @param skyrocket_updates_filename: (str) csv containing raw satellite data extracted from skyrocket
    '''  
    
    print("")
    print("Begin Skyrocket webscraper...")
    
    # Connect to SQL database    
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()    
    
    # Create list of webpages in SkyRocket satellite directory - filter for satellites
    
    ##Define parent webpages for satellite listings
    url_home = "https://space.skyrocket.de/"
    url_dir = url_home + "directories/"
    url_sat = url_dir + "sat.htm"
    html = requests.get(url = url_sat).text
    soup = BeautifulSoup(html, "html.parser")
    ##Create list of html tags for satellite application-country webpages
    tags = soup.find_all("ul", class_="country-list mcol2")
    ##Create url from tags
    urls = {}
    for t in tags:
        for a in t.findAll("a"):
            urls[a["href"].split(".htm")[0]] = [url_dir + a["href"]]
        
    ##Extract webpages from parent webpages
    urls_sats = dict([(key,[]) for key in urls.keys()])
    for key, url_ref in urls.items():
        html = requests.get(url = url_ref[0]).text
        soup = BeautifulSoup(html, "html.parser")
        tags = soup("td")
        for t in tags:
            for a in t.findAll("a"):
                tmp = urls_sats[key]
                tmp.append(url_home + a["href"][3:])
                urls_sats[key] = tmp
                
    ##flatten urls into list
    url_list = sum(list(urls_sats.values()),[])
    
    ##Remove urls related to launch vehicles
    url_list_tmp = [a for a in url_list if re.search("(.*)\/doc_lau(.*)", a) is None]
    
    ##Extract unique URLs
    url_list_new = list(set(url_list_tmp))
    
    ##Add list of URLs to SQL database
    url_df = pd.DataFrame(url_list_new, columns = ["url"])
    url_df.to_sql("url_skyrocket", conn, if_exists="replace", index=False)
    
    # Extract data from webpages and dump into SQL table    
    
    ##Define inner function for scraping data from html tables
    def col_search(search_type, regex_str, tbl_in):
        if tbl_in is not None:
            if search_type == 0:
                tbl_in.reset_index(drop=True, inplace=True)
                ind = tbl_in[0].str.upper().str.extract(regex_str).dropna(thresh=1).index
                if len(ind) > 0:
                    return tbl_in[1].iloc[ind[0]]
            elif search_type == 1:
                ind = tbl_in.columns[tbl_in.columns.str.upper().str.extract(regex_str).dropna(thresh=1).index]
                if len(ind) > 0:
                    return tbl_in[ind[0]]
        return
    
    # Regex mapping for columns to extract
    col_dict = {"ObjectName": {"tbl_num": 1, "regex_str": "(.*)(SATELLITE)(.*)"},
            "OrbitClass": {"tbl_num": 0, "regex_str": "(.*)(ORBIT)(.*)"},
            "LaunchDate": {"tbl_num": 1, "regex_str": "(.*)(DATE)(.*)"},
            "Purpose": {"tbl_num": 0, "regex_str": "(.*)(TYPE)(.*)|(.*)(APPLICATION)(.*)"},
            "LaunchMass": {"tbl_num": 0, "regex_str": "(.*)(MASS)(.*)"},
            "Owner": {"tbl_num": 0, "regex_str": "(.*)(NATION)(.*)"},
            "LaunchVehicle": {"tbl_num": 1, "regex_str": "(.*)(VEHICLE)(.*)|(.*)(LAUNCHER)(.*)"}}
    
    # Create SQL table for data dump
    satcat_new = pd.DataFrame(columns = [a for a in col_dict.keys()] + ["description","URL","lastupdate"])
    try:
        satcat_new.to_sql("satcat_skyrocket", conn, if_exists="replace", index=False)
    except Exception:
        pass
    
    # Extract data and dump into SQL table
    
    url_missing = []
    for n, url_sat in enumerate(url_list_new):
        print(url_sat)
        print("")
        print(n, "/", len(url_list_new))
        print("------")
        df  = pd.DataFrame(columns = satcat_new.columns)
        try:
            tmp = pd.read_html(url_sat)
        except Exception:
            pass 
            url_missing.append(url_sat)
            continue
        #Extract last update date from webpage
        html = requests.get(url = url_sat).text
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all("div", class_ ="footerdate")
        lastupdate = re.findall("Last update:(.*)",tags[0].contents[0])[0].strip()    
        #Check if page has been updated since last extract
        ## Check database
        query = 'select lastupdate from satcat_skyrocket where url = "{}"'.format(url_sat)
        cur.execute(query)
        lu = cur.fetchone()
        add_row = False
        if lu is not None:
            if lu != lastupdate:
                add_row = True
        else:
            add_row = True
        #Update scraped data for existing entry
        if add_row:
            # Extract info from tables in webpage
            tbl_tmp = [None, None]
            # Check if correct tables extracted from html page
            # Extract two tables: 
            # table (1) - 0/1 as column names - contains satellite purpose, mass, owner
            # table (2) - Satellite, Launch vehicle etc. as column names
            for i in range(0,len(tmp)):
                # Fix for multilevel columns
                tmp[i].columns = list(tmp[i].columns.get_level_values(0))
                try:
                    tmp[i].columns = tmp[i].columns.str.upper()
                    tbl_tmp[1] = tmp[i]
                except Exception:
                    pass
                    tmp[i].dropna(inplace=True) #Remove NaN rows
                    if len(sum([[row for row in tmp[i][0].str.upper() if re.match(a["regex_str"],row) ] for a in col_dict.values()],[])) > 0:
                        tbl_tmp[0] = tmp[i]
                    else:
                        continue
                #Loop through list of column mappings dicts
                for colname, map_dict in col_dict.items():
                    df[colname] = col_search(map_dict["tbl_num"], map_dict["regex_str"], tbl_tmp[map_dict["tbl_num"]])
            df["lastupdate"] = lastupdate
            df["URL"] = url_sat
            # Add satellite description text
            html2 = requests.get(url = url_sat).text
            soup2 = BeautifulSoup(html, "html.parser")
            tags2 = soup.find_all("div", id ="satdescription")
            try:
                df["description"] = re.sub('"',"'",unidecode.unidecode(" ".join(tags2[0].text.splitlines()).strip()))
            except Exception:
                pass
                df["description"] = ""
            # Update rows in sql table
            ##delete old rows
            query = 'delete from satcat_skyrocket where url = "{}"'.format(url_sat)
            cur.execute(query)
            conn.commit()
            ##insert new rows
            for index,rows in df.iterrows():
                query = 'insert into satcat_skyrocket values("' + '","'.join([re.sub('"',"'",str(rows[c])) for c in df.columns]) + '")'
                cur.execute(query)
                conn.commit()

    print("Satellite data extracted from Skyrocket website!")
    
    return

def enrich_satcat(dbs_name, enriched_satcat_filename):
    ''' 
    Import merged satellite catalogue data from SQL database

    @param dbs_name: (str) name of sqlite database to write in merged satallite catalogue data
    ''' 
  
    print("")
    print("Enriching satellite catalogue data with webscraped data")
    print("")

    ##Connect to SQL database    
    sqlite_dbs = ".\\dat\\clean\\" + dbs_name
    conn = sqlite3.connect(sqlite_dbs)
    cur = conn.cursor()        
    
    # Extract satellite catalogue data from SQL database
    
    # Extract all rows
    query = "select * from satcat"
    cur.execute(query)
    satcat_temp = cur.fetchall()
    # Extract column names 
    query = "pragma table_info(satcat)"
    cur.execute(query)
    cols = [a[1] for a in cur.fetchall()]
    # Create data frame
    satcat_pre = pd.DataFrame(satcat_temp, columns = cols)        
    
    
    # Extract raw skyrocket data from SQL database
    
    ##Extract rows from table
    query = "select * from satcat_skyrocket"
    cur.execute(query)
    satcat_sr_rows = cur.fetchall()
    ##Fetch table column names
    query = "pragma table_info(satcat_skyrocket)"
    cur.execute(query)
    cols = [a[1] for a in cur.fetchall()]
    ##Create dataframe
    satcat_sr_raw = pd.DataFrame(satcat_sr_rows, columns = cols)    
    
    # Clean Satellite Names - standardise, remove duplicates, unique name per row
    
    satcat_sr = satcat_sr_raw.copy()
    
    ##Split satellite name entries by non-alphanumeric or non-space character - precursor to enforcing uniqueness
    satcat_sr["ObjectName"] = satcat_sr["ObjectName"].str.split('[^a-zA-Z0-9\s-]').apply(lambda x:  [a.strip() for a in x] if isinstance(x, list) else x)
    
    ##Explode dataframe - individual satellite name per row
    skyrocket_df = satcat_sr.explode("ObjectName")
    ##Standardise satellite names
    skyrocket_df["ObjectName"] = skyrocket_df["ObjectName"].astype(str).str.upper().str.replace("[ ]+"," ", regex=True)
    ##Standardise launch vehicle names
    skyrocket_df["LaunchVehicle"] = skyrocket_df["LaunchVehicle"].astype(str).str.replace("[ ]+"," ", regex=True)
    ##Standardise launch date
    skyrocket_df["LaunchDate"] = skyrocket_df["LaunchDate"].astype(str)
    ##Remove duplicates
    skyrocket_df.drop_duplicates(subset=["ObjectName","LaunchVehicle"], inplace=True)
    skyrocket_df.drop_duplicates(subset=["ObjectName","LaunchDate"], inplace=True)
    skyrocket_df.dropna(subset=["ObjectName"], inplace=True)
    ##Remove rows with empty or single character names
    skyrocket_df = skyrocket_df[~(skyrocket_df["ObjectName"] == '') & (skyrocket_df["ObjectName"].str.len() > 1)]
    skyrocket_df.reset_index(inplace=True, drop=True)    
    
    # Merge scraped data to rows in satellite catalogue by closest satellite name match
    
    ##Fix for language differences (C interchangeable w/ k)
    alphnum = dict([(str(l),[str(l)]) for l in list(string.ascii_uppercase) + list(range(0,10)) ])
    alphnum["C"] = ["C","K"]
    ##Compute edit distance between satellite names in satellite catalogue and skyrocket data
    dist_matrix = np.ones((satcat_pre.shape[0],skyrocket_df.shape[0]))*999
    print("Computing edit distance between satellite names in existing catalogue and skyrocket data")    
    for n, sat in enumerate(satcat_pre["ObjectName"]):
        print("")
        satname_new = re.sub("[-]"," ",sat).split("(")[0].split("&")[0].split("[")[0]
        print(satname_new)
        print("{}/{} ".format(n,satcat_pre.shape[0]))
        print("")
        print("-------")
        regex_str = "(^" + ".*|^".join(alphnum[sat[0]]) + ".*)"
        indices = skyrocket_df.ObjectName.str.extract(regex_str).dropna().index
        dist_matrix[n, indices] = np.array([nltk.edit_distance(satname_new,re.sub("[-]"," ",s)) for s in skyrocket_df.loc[indices,"ObjectName"]])
    ##Convert distance matrix to dataframe
    dist_matrix_df = pd.DataFrame(dist_matrix, index = satcat_pre["ObjectName"], columns = skyrocket_df["ObjectName"] + "_" + skyrocket_df["LaunchDate"].astype(str))
    dist_matrix_df.head()
    ##Assign skyrocket row index to satellite name from satcat subset
    tol = 1
    matches = {}
    tols = dict([(name,999) for name in dist_matrix_df.index])
    for n, col in enumerate(dist_matrix_df.columns):
        indx = dist_matrix_df[col]<=tol
        tol_vals = dist_matrix_df[col][indx]
        name_matches = list(dist_matrix_df.index[indx])
        #Assign index if edit distance is below tolerance
        if len(name_matches):
            for name, t in zip(name_matches,tol_vals):
                #Retain match with lowest edit distance below tolerance
                if t < tols[name]:
                    matches[name] = n
                    tols[name] = t       
    ##Retain satellites w/ matches to skyrocket data and merge on Purpose and Launch Vehicle columns
    df_to_merge = pd.DataFrame(columns=["ObjectName","Purpose","LaunchVehicle"])
    df_to_merge["ObjectName"] = matches.keys()
    for col in df_to_merge.drop(columns=["ObjectName"]).columns:
        df_to_merge[col] = skyrocket_df[col][matches.values()].values          
    ##Merge new columns onto satellite catalogue subset
    tmp_merge = pd.merge(satcat_pre, df_to_merge, how="left", on="ObjectName")
    
    # Data processing I - map Launch vehicle data to launch vehicle class and merge
    
    ##Convert launch vehicle column to launch vehicle class and coalesce with existing catalogue data
    tmp_merge["LaunchVehicle"] = tmp_merge["LaunchVehicle"].astype(str).str.strip()
    tmp = tmp_merge["LaunchVehicleClass"].apply(lambda x: None if x == "Unknown" else x)
    tmp_merge["LaunchVehicleClass"] = tmp.combine_first(pd.Series([re.sub("[\s]{2,}"," ",
                                                   re.sub("[.\-\(\)]"," ",a)).rsplit(" ",1)[0].
                                                   rsplit(" ",1)[0].
                                                   rsplit(" ",1)[0].
                                                   rsplit(" ",1)[0].
                                                   rsplit(" ",1)[0].
                                                   rsplit(" ",1)[0].strip() 
                                                   for a in tmp_merge["LaunchVehicle"]])).replace("nan", "Unknown")    
    ##Apply launch vehicle class mapping
    def manual_mapper(dat,col,str_old,str_new):
        dat.loc[dat[col].isin(str_old), col] = str_new
        return dat
    lv_map = {"Long March":["Long","CZ"], "Soyuz":["Soyuz Fregat Soyuz","Souyz"], "LauncherOne":["Launcher"],
             "Proton":["Proton/Breeze","Proton M Briz"],"ISS NRCSD":['Dextre Arm + Kaber', 'Nanoracks','J',
                                                    'KIBO','SEOPS','JEM','Kaber'],
              "Black Arrow":["Black"], "Start-1":["Start"], "Titan":["Commercial"], "L1011 Stargazer":["L1011"],
              'Kaituozhe': ["KT"],'JAXA H':["H"],'JAXA Mu': ["M",'JAXA','JAXA M-V'], 'JAXA N':["N"]}
    for u,v in lv_map.items():
        tmp_merge2 = manual_mapper(tmp_merge,"LaunchVehicleClass",v,u)    
        
    # Data processing II - update use type in satellite catalogue using purpose column from skyrocket data
    
    ##Replace nans with "unknown" in skyrocket data
    tmp_merge2.Purpose_y.fillna("Unknown")    
    ##Update use type for satellites with military in skyrocket purpose data
    tmp_merge3  = tmp_merge2.copy()
    indx = tmp_merge3["Purpose_y"].fillna("Unknown").str.upper().str.match(".*(MILITARY).*")
    tmp_merge3.loc[indx,"UseType"] = tmp_merge3["UseType"][indx].replace("Unknown","Military")    
    ##Drop extra columns
    tmp_merge3["Purpose"] = tmp_merge3["Purpose_x"]
    cols_to_drop = [item for  item in tmp_merge3.columns if re.search('(.*\_x|.*\_y)',item)] + ["LaunchVehicle"]
    enriched_satcat = tmp_merge3.drop(columns = cols_to_drop)
    
    # Export data to csv
    
    filename = ".\\dat\\clean\\" + enriched_satcat_filename    
    enriched_satcat.to_csv(filename, index=False)
    
    print("Satellite catalogue data enriched!")
    
    return
    