import sqlite3
import pandas as pd
from os import path
from shutil import copy, copytree, rmtree

from DIRS import PATHS

def copy_original_data():
    MODIFIED_DATA = PATHS['MODIFIED_DATA']
    ORIGINAL_DATA = PATHS['ORIGINAL_DATA']
    print(f'copying all data to {MODIFIED_DATA}')
    if path.exists(MODIFIED_DATA):
        rmtree(MODIFIED_DATA)
    copytree(ORIGINAL_DATA, MODIFIED_DATA)


year = lambda y : ('0' if y < 10 else '')+str(y)


def create_unemployment_per_year():
    print('creating unemployment tables')

    ROOT = PATHS['MODIFIED_DATA']
    CSV_ROOT = f'{ROOT}/csv'
    DB_ROOT = f'{ROOT}/db'
    UNEMP_DB_SOURCE = f'{DB_ROOT}/state_unemployment.db'
    UNEMP_CSV_PATH = f'{CSV_ROOT}/unemployment/unemployment_07_11.csv'

    title_state = lambda s: s.title()
    converters = dict( list({'State': title_state}.items()) + list({f"20{year(y)}": eval for y in range(7, 12)}.items()))
    unemployment_data = pd.read_csv(UNEMP_CSV_PATH, converters=converters)

    conn = sqlite3.connect(UNEMP_DB_SOURCE)
    
    unemployment_data.to_sql('all_unemployment', conn, if_exists='replace', index=False)
    cur = conn.cursor()
    
    for y in range(7, 12):
        f_year = year(y)
        print(f'--> unemployment for year: {f_year}')
        q = f'''
        create table state_unemployment_{f_year} as 
            select State as state, "20{f_year}" as unemployment_percent_20{f_year} 
            from all_unemployment
        '''
        cur.execute(q)
        conn.commit()
    cur.execute('drop table all_unemployment')
    conn.commit()
    conn.close()


def create_populations_per_year():
    print('creating population tables')

    ROOT = PATHS['MODIFIED_DATA']
    CSV_ROOT = f'{ROOT}/csv'
    DB_ROOT = f'{ROOT}/db'
    POP_CSV_SOURCE = f'{CSV_ROOT}/population/state_populations_2000_to_2019.csv'
    POP_DB_SOURCE = f"{DB_ROOT}/state_populations.db"

    title_state = lambda s: s.title()
    converters = dict( list({'State': title_state}.items()) + list({f'pop_20{year(y)}': eval for y in range(0, 20)}.items()))
    population_data = pd.read_csv(POP_CSV_SOURCE, converters=converters)
    population_data = population_data.drop(columns=[f'pop_20{year(y)}' for y in range(0, 20) if y < 7 or y > 11])

    # remove post-fixed 0s
    for index_label, row_series in population_data.iterrows():
       population_data.at[index_label , 'state_FIPS'] = int(row_series['state_FIPS'])/1000

    conn = sqlite3.connect(POP_DB_SOURCE)
    population_data.to_sql('all_pops', conn, if_exists='replace', index=False)
    cur = conn.cursor()

    for y in range(7, 12):
        f_year = year(y)
        print(f'--> population totals for year: {f_year}')
        q = f'''
        create table pop_state_{year(y)} as 
            select state_name as state, state_FIPS as fips, pop_20{f_year} as population_20{f_year} 
            from all_pops;
        '''
        cur.execute(q)
        conn.commit()
    cur.execute('drop table all_pops')
    conn.commit()
    conn.close()


def create_deaths_per_year():
    print('creating suicide total tables per year')

    ROOT = PATHS['MODIFIED_DATA']
    CSV_ROOT = f'{ROOT}/csv'
    DB_ROOT = f'{ROOT}/db'
    DEATHS_CSV_SOURCE = f'{CSV_ROOT}/deaths/deaths.csv'
    DEATHS_DB_SOURCE = f"{DB_ROOT}/state_suicides.db"

    title_state = lambda s: s.title()
    int_deaths = lambda s: int(s.replace(',',''))
    needed_cols = ['Year',  'Cause Name', 'State', 'Deaths']
    suicide_data = pd.read_csv(DEATHS_CSV_SOURCE, converters={'State': title_state, 'Year': eval, 'Deaths': int_deaths})

    suicide_data.drop(suicide_data[(suicide_data.Year < 2007) | (suicide_data.Year > 2011)].index, inplace=True)
    suicide_data.drop(suicide_data[suicide_data['Cause Name'] != 'Suicide'].index, inplace=True)
    suicide_data.drop(columns=[col for col in suicide_data if col not in needed_cols], inplace=True)

    conn = sqlite3.connect(DEATHS_DB_SOURCE)
    suicide_data.to_sql('all_suicides', conn, if_exists='replace', index=False)
    cur = conn.cursor()

    for y in range(7, 12):
        f_year = year(y)
        print(f'--> suicide totals for year: {f_year}')
        q = f'''
        create table suicide_state_{f_year} as 
            select Year as year, State as state, Deaths as deaths 
            from all_suicides where year = 20{f_year};
        '''
        cur.execute(q)
        conn.commit()
    cur.execute('drop table all_suicides')
    conn.commit()
    conn.close()


def create_populations_deaths_per_year():
    print('combining population totals and suicide totals tables per year')

    DB_ROOT = PATHS['MODIFIED_DATA']
    SUI_DB_SOURCE = f"{DB_ROOT}/db/state_suicides.db"
    POP_DB_SOURCE = f"{DB_ROOT}/db/state_populations.db"
    POP_SUI_DB_SOURCE = f"{DB_ROOT}/db/state_pop_suicides.db"
    copy(SUI_DB_SOURCE, POP_SUI_DB_SOURCE)

    con = sqlite3.connect(POP_SUI_DB_SOURCE)
    con.execute("attach database '"+POP_DB_SOURCE+"' as state_pops;")
    cur = con.cursor()

    for y in range(7, 12):
        f_year = year(y) 
        print(f'--> population/suicide totals for year: {f_year}')

        cur.execute(
            f'''
            create table state_pop_suicides_{f_year} as
                select state, fips, population_20{f_year}, suicides, 
                100*(cast(suicides as double)/population_20{f_year}) as suicide_percent 
                from (
                    select * from (
                        select state, fips, population_20{f_year} 
                        from 
                        state_pops.pop_state_{f_year}
                    )
                    join (
                        select state, deaths as suicides from suicide_state_{f_year}
                    ) 
                    using (state)
                );
            '''
        )
        con.commit()
        cur.execute(f'drop table suicide_state_{f_year}')
        con.commit()
    con.close()


def create_suicides_unemployment_per_year():
    print('combining population, suicide, unemployment tables per year')

    DB_ROOT = PATHS['MODIFIED_DATA']
    UNEMP_DB_SOURCE = f"{PATHS['MODIFIED_DATA']}/db/state_unemployment.db"
    POP_SUI_DB_SOURCE = f"{DB_ROOT}/db/state_pop_suicides.db"
    UNEMP_SUI_DB_SOURCE = f"{DB_ROOT}/db/state_suicides_unemployment.db"
    copy(UNEMP_DB_SOURCE, UNEMP_SUI_DB_SOURCE)

    con = sqlite3.connect(UNEMP_SUI_DB_SOURCE)
    con.execute("attach database '"+POP_SUI_DB_SOURCE+"' as state_pop_sui;")

    cur = con.cursor()
    for y in range(7, 12):
        f_year = year(y) 
        print(f'--> unemployment/population/suicide totals for year: {f_year}')

        cur.execute(
            f'''
            create table state_suicide_unemployment_{f_year} as
                select *, ntile(3) over (order by unemployment_percent) || "." || ntile(3) over (order by suicide_percent) as bimode
                from (
                    select state, fips, population_20{f_year} as population, suicides, suicide_percent, unemployment_percent_20{f_year} as unemployment_percent,
                    100*(suicide_percent/unemployment_percent_20{f_year}) as suicide_unemployment_ratio_percent
                    from (
                        select * from (
                            select state, fips, population_20{f_year}, suicides, suicide_percent
                            from 
                            state_pop_sui.state_pop_suicides_{f_year}
                        )
                        join (
                            select state, unemployment_percent_20{f_year} from state_unemployment_{f_year}
                        ) 
                        using (state)
                    )
                ) order by state;
            '''
        )
        con.commit()
        cur.execute(f'drop table state_unemployment_{f_year}')
        con.commit()
    con.close()


def create_suicides_unemployment_geometry_per_year():
    print('creating geomtetry/unemployment/population/suicide tables per year')

    DB_ROOT = f"{PATHS['MODIFIED_DATA']}/db"
    STATES_GEO_DB_SOURCE = f'{DB_ROOT}/states_geometry.db'
    UNEMP_SUI_DB_SOURCE = f'{DB_ROOT}/state_suicides_unemployment.db'
    UNEMP_SUI_GEO_DB_SOURCE = f'{DB_ROOT}/state_suicides_unemployment_geometry.db'
    copy(UNEMP_SUI_DB_SOURCE, UNEMP_SUI_GEO_DB_SOURCE)

    con = sqlite3.connect(UNEMP_SUI_GEO_DB_SOURCE)
    con.execute("attach database'"+STATES_GEO_DB_SOURCE+"' as states_geo;")
    cur = con.cursor()

    cur.execute('create table geometry_columns as select * from states_geo.geometry_columns;')
    con.commit()
    cur.execute('delete from  geometry_columns where f_table_name = "states_geometry"');
    con.commit()

    for y in range(7, 12):
        f_year = year(y)
        print(f'--> unemployment/population/suicide totals for year: {f_year}')
        cur.execute(
            f'''
            create table state_suicide_unemployment_geo_{f_year} as
                select * from (
                    select ogc_fid, GEOMETRY, fid, state_name as state from states_geo.states_geometry
                ) join (
                    select state, fips, population, suicides, suicide_percent,
                           unemployment_percent, suicide_unemployment_ratio_percent, bimode
                    from state_suicide_unemployment_{f_year}
                ) using(state);
            '''
        )
        con.commit()

        cur.execute(
            f'''
            insert into geometry_columns(f_table_name, f_geometry_column, geometry_type, coord_dimension, geometry_format)
            values("state_suicide_unemployment_geo_{f_year}", "GEOMETRY", 6, 2, "WKB");
            '''
        )
        con.commit()

        cur.execute(f'drop table state_suicide_unemployment_{f_year}')
        con.commit()

    con.close()


def clean_and_create():
    copy_original_data()
    create_populations_per_year()
    create_deaths_per_year()
    create_populations_deaths_per_year()
    create_unemployment_per_year()
    create_suicides_unemployment_per_year()
    create_suicides_unemployment_geometry_per_year()

if __name__ != '__main__': pass
