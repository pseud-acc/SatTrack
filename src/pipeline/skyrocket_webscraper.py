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
    
    # Add list of skyrocket webpages to database
    
    ##Create url table if does not exist
    query = '''CREATE TABLE IF NOT EXISTS url_skyrocket
            (urlid INTEGER PRIMARY KEY,
            urlname varchar(200) NOT NULL,
            lastupdate varchar(200) NOT NULL,
            updateflag varchar(2) NOT NULL,
            matchupdateflag varchar(2) NOT NULL)'''
    cur.execute(query)
    conn.commit()
        
    ##Upsert data in URL table
    print("Checking skyrocket website for new urls and updates...")
    for n,url_sat in enumerate(url_list_new):
        print(url_sat,n+1,"/",len(url_list_new))
        # Extract last update date from html text
        html = requests.get(url = url_sat).text
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all("div", class_ ="footerdate")
        lastupdate = re.findall("Last update:(.*)",tags[0].contents[0])[0].strip()    
        query = "select lastupdate from url_skyrocket where urlname = '" + url_sat + "'"
        cur.execute(query)
        url_lastupdate_output = cur.fetchall()
        # Insert url into table if not already in database
        if len(url_exists_output) < 1:
            print("url not in database")
            print("")
            insert_row = [url_sat,lastupdate,"Y","Y"]
            query = "insert into url_skyrocket(urlname,lastupdate,updateflag,matchupdateflag) values('" + "','".join(insert_row) + "')"
            cur.execute(query)
            conn.commit()
        else:
            print("url in database - checking last update")
            # Trigger update flag if last update date has changed
            if url_lastupdate_output[0] != lastupdate:
                upsert_row = [lastupdate,"Y"]
            else:
                upsert_row = [lastupdate,"N"]
            query = '''update url_skyrocket 
                        set lastupdate = "{}", 
                            updateflag = "{}", 
                            matchupdateflag = "{}" WHERE urlname="{}"'''.format(upsert_row[0],upsert_row[1],upsert_row[1])
            cur.execute(query) 
            
            
    # Create table to track matches between satellites in catalogue and skyrocket webpages        
    
    ##Create matching table if does not exist
    query = '''
            CREATE TABLE IF NOT EXISTS match_satcat_url_skyrocket
            (satcatid INTEGER PRIMARY KEY,
            skyrocketid INTEGER)
            '''
    cur.execute(query)
    conn.commit()
            
    ##Update matching table
    query  = '''
            INSERT INTO match_satcat_url_skyrocket 
            SELECT SatCatId, null 
            FROM satcat 
            WHERE SatCatId not in (SELECT SatCatId FROM match_satcat_url_skyrocket)
    '''
    cur.execute(query)
    conn.commit()            
    
    
    # Scrape data from skyrocket webpages and dump in database
    
    ##Function for webscraping
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

    ##Regex mapping for columns to extract
    col_dict = {"ObjectName": {"tbl_num": 1, "regex_str": "(.*)(SATELLITE)(.*)"},
                "OrbitClass": {"tbl_num": 0, "regex_str": "(.*)(ORBIT)(.*)"},
                "Operator": {"tbl_num": 0, "regex_str": "(.*)(OPERATOR)(.*)"},
                "LaunchDate": {"tbl_num": 1, "regex_str": "(.*)(DATE)(.*)"},
                "Purpose": {"tbl_num": 0, "regex_str": "(.*)(TYPE)(.*)|(.*)(APPLICATION)(.*)"},
                "LaunchMass": {"tbl_num": 0, "regex_str": "(.*)(MASS)(.*)"},
                "Owner": {"tbl_num": 0, "regex_str": "(.*)(NATION)(.*)"},
                "LaunchVehicle": {"tbl_num": 1, "regex_str": "(.*)(VEHICLE)(.*)|(.*)(LAUNCHER)(.*)"}}  
    
    ##Create table to input data
    satcat_new = pd.DataFrame(columns = [a for a in col_dict.keys()] + ["description","urlid"])
    try:
        satcat_new.to_sql("satcat_skyrocket", conn, if_exists="fail", index=False)
    except Exception:
        pass
            
    ##Extract updated urls
    query = "select urlname,urlid from url_skyrocket where updateflag = 'Y'"
    cur.execute(query)
    urls_to_run = cur.fetchall()
    ##Extract data from htmls of urls - delete and replace existing urls
    for n, url_sat_id in enumerate(urls_to_run):
        url_sat = url_sat_id[0]
        url_id = url_sat_id[1]
        print(url_sat)
        print("")
        print(n, "/", len(urls_to_run))
        print("------")
        ## Update url database
        query = "update url_skyrocket set updateflag = 'N' where urlid = {}".format(url_id)
        cur.execute(query)
        ## Check database    
        df  = pd.DataFrame(columns = satcat_new.columns)
        try:
            tmp = pd.read_html(url_sat)
        except Exception:
            pass 
            url_missing.append(url_sat)
            continue
        #Upsert scraped data for url
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
        df["urlid"] = url_id
        #Add satellite description text
        html = requests.get(url = url_sat).text
        soup = BeautifulSoup(html, "html.parser")
        tags = soup.find_all("div", id ="satdescription")
        try:
            df["description"] = re.sub('"',"'",unidecode.unidecode(" ".join(tags[0].text.splitlines()).strip()))
        except Exception:
            pass
            df["description"] = ""
        # Update rows in sql table
        ## delete old rows
        query = 'delete from satcat_skyrocket where urlid = "{}"'.format(url_id)
        cur.execute(query)
        conn.commit()
        ## insert new rows
        for index,rows in df.iterrows():
            query = 'insert into satcat_skyrocket values("' + '","'.join([re.sub('"',"'",str(rows[c])) for c in df.columns]) + '")'
            cur.execute(query)
            conn.commit()
    
    conn.close()
 

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
    
    # Add processed skyrocket data to database
    
    ##Add table to database
    query = '''CREATE TABLE IF NOT EXISTS satcat_skyrocket_norm
                (skyrocketid INTEGER PRIMARY KEY,
                urlid INTEGER NOT NULL,
                ObjectName TEXT NOT NULL,
                OrbitClass TEXT,
                Operator TEXT,
                LaunchDate TEXT,
                Purpose TEXT,
                LaunchMass TEXT,
                Owner TEXT,
                LaunchVehicle TEXT,
                description TEXT
                )'''
    cur.execute(query)
    conn.commit()    
    
    ## Delete rows if url data has been updated
    query = "DELETE FROM satcat_skyrocket_norm WHERE urlid in (SELECT urlid FROM url_skyrocket WHERE matchupdateflag = 'Y')"
    cur.execute(query)
    conn.commit()
    
    # Insert new data
    cols_to_input = ["urlid","ObjectName","OrbitClass","Operator","LaunchDate",
                     "Purpose","LaunchMass","Owner","LaunchVehicle","description"]
    query = "select distinct ObjectName || '_' || LaunchDate || '_' || LaunchVehicle from satcat_skyrocket_norm"
    cur.execute(query)
    unique_id_list = [a[0] for a in cur.fetchall()]
    for index, row in skyrocket_df.iterrows():
        unique_id = "_".join(row[["ObjectName","LaunchDate","LaunchVehicle"]])
        if unique_id not in unique_id_list:
            query = "INSERT INTO satcat_skyrocket_norm(" + ",".join(cols_to_input) + ") values(" + str(row[cols_to_input[0]]) + ',"' + '","'.join(row[cols_to_input[1:]]) + '")'
            cur.execute(query)
            conn.commit()    
    
    # Merge scraped data to rows in satellite catalogue by closest satellite name match
    
    ##Select satellites from satcat without matching skyrocket url or where skyrocket url has been updated
    query = """ with matchflag_url as (
                select 
                    m.satcatid, coalesce(u.matchupdateflag,'Y') as flag
                from 
                    match_satcat_url_skyrocket m
                left join
                    satcat_skyrocket_norm s
                on m.skyrocketid = s.skyrocketid
                left join
                    url_skyrocket u
                on s.urlid = u.urlid
                )
            select 
                m.satcatid, s.ObjectName 
            from 
                matchflag_url m
            left join 
                satcat s
            on s.satcatid = m.satcatid
            where m.flag <> "N"
            and s.satcatid is not null
            """
    cur.execute(query)
    output = cur.fetchall()
    satellite_match_list = [a[1] for a in output]
    id_match_list = [a[0] for a in output]
    
    ##Read normalised skyrocket data
    query = "select * from satcat_skyrocket_norm"
    cur.execute(query)
    output = cur.fetchall()
    query = "pragma table_info(satcat_skyrocket_norm)"
    cur.execute(query)
    cols = [a[1] for a in cur.fetchall()]
    skyrocket_df = pd.DataFrame(output, columns = cols)
    skyrocket_df.set_index("skyrocketid", inplace = True) 
    
    ##Convert skyrocket index to array row index
    index_to_array_index = pd.Series(range(0,skyrocket_df.shape[0]), index = skyrocket_df.index)
    
    ##Fix for language differences (C interchangeable w/ k)
    alphnum = dict([(str(l),[str(l)]) for l in list(string.ascii_uppercase) + list(range(0,10)) ])
    alphnum["C"] = ["C","K"]
    ##Compute edit distance between satellite names in satellite catalogue and skyrocket data
    dist_matrix = np.ones((len(satellite_match_list),skyrocket_df.shape[0]))*999
    print("Computing edit distance between satellite names in existing catalogue and skyrocket data")    
    for n, sat in enumerate(satellite_match_list):
        print("")
        satname_new = re.sub("[-]"," ",sat).split("(")[0].split("&")[0].split("[")[0]
        print(satname_new)
        print("{}/{} ".format(n+1,len(satellite_match_list)))
        print("")
        print("-------")
        regex_str = "(^" + ".*|^".join([a + sat[1] for a in alphnum[sat[0]]]) + ".*)"
        indices = skyrocket_df.ObjectName.str.extract(regex_str).dropna().index
        dist_matrix[n, index_to_array_index[indices]] = np.array([nltk.edit_distance(satname_new,re.sub("[-]"," ",s)) for s in skyrocket_df.loc[indices,"ObjectName"]])
    ##Convert distance matrix to dataframe
    dist_matrix_df = pd.DataFrame(dist_matrix, index = satellite_match_list, columns = skyrocket_df["ObjectName"] + "_" + skyrocket_df["LaunchDate"].astype(str))
    dist_matrix_df.head()
    ##Assign skyrocket row index to satellite name from satcat subset
    tol = 1
    satname_matches = {}
    satid_matches = {}
    tols = dict([(name,999) for name in dist_matrix_df.index])
    for n, col in zip(skyrocket_df.index,dist_matrix_df.columns):
        indx = dist_matrix_df[col]<=tol
        tol_vals = dist_matrix_df[col][indx]
        name_matches = list(dist_matrix_df.index[indx])
        id_matches = np.array(id_match_list)[list(indx.values)]
        #Assign index if edit distance is below tolerance
        if len(name_matches):
            for name, t, idm in zip(name_matches,tol_vals,id_matches):
                #Retain match with lowest edit distance below tolerance
                if t < tols[name]:
                    satname_matches[name] = n
                    satid_matches[str(idm)] = n
                    tols[name] = t
    ##Update database with satellites matched to skyrocket webpages
    for satid,n in satid_matches.items():
        query = """ UPDATE match_satcat_url_skyrocket set skyrocketid = {} WHERE SatCatId = {}""".format(n, int(satid))
        cur.execute(query)
        conn.commit()
    ##Update match flag in url_skyrocket table in database
    query = """
            UPDATE url_skyrocket
            SET matchupdateflag = "N"
            WHERE 1=1
    """
    cur.execute(query)
    conn.commit()
    ##Define satellites with matching skyrocket data
    query = "select satcatid, skyrocketid from match_satcat_url_skyrocket where skyrocketid not null"
    cur.execute(query)
    output = cur.fetchall()
    satid_list = [int(a[0]) for a in output]
    skyrocketid_list = [int(a[1]) for a in output]    
    ##Retain satellites w/ matches to skyrocket data and merge on Purpose and Launch Vehicle columns
    df_to_merge = pd.DataFrame(columns=["SatCatId","Purpose","LaunchVehicle"])
    df_to_merge["SatCatId"] = satid_list
    for col in df_to_merge.drop(columns=["SatCatId"]).columns:
        df_to_merge[col] = skyrocket_df.loc[skyrocketid_list,col].values    
    ##Merge new columns onto satellite catalogue subset
    tmp_merge = pd.merge(satcat_pre, df_to_merge, how="left", on="SatCatId")
    
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
    lv_map = {"Long March":["Long","CZ"], "Soyuz":["Soyuz Fregat Soyuz","Souyz","11A510"], "LauncherOne":["Launcher"],
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
    