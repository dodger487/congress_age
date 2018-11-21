import json

import numpy as np
import pandas as pd


def make_rows(cngrs_prsn):
  """Output a list of dicitonaries for each JSON object representing a 
  congressperson.

  Each individaul dictionary will contain information about the congressperson 
  as well as info about their term.
  """
  name = cngrs_prsn["name"]["first"] + " " + cngrs_prsn["name"]["last"]
  birthday = cngrs_prsn["bio"].get("birthday", None)
  gender = cngrs_prsn["bio"]["gender"]

  terms = cngrs_prsn["terms"]
  rows = []
  for t in terms:
    row = {}
    row["name"] = name
    row["birthday"] = birthday
    row["gender"] = gender

    row["term_start"] = t["start"]
    row["term_end"] = t["end"]
    
    row["term_type"] = t["type"]
    row["party"] = t.get("party")  # Defaults to None
    rows.append(row)

  return rows


def load_df_from_files():
  """Create a DataFrame 
  """
  with open("legislators-historical.json") as f:
    data_old = json.load(f)

  with open("legislators-current.json") as f:
    data_new = json.load(f)

  data = data_old + data_new

  rows = []
  for person in data:
    try:
      these_rows = make_rows(person)
    except:
      print(person)
    rows.extend(these_rows)

  df = pd.DataFrame(rows)
  return df 


def clean_df(df):
  """Transform types and filter some data."""
  # TODO: get birthdays for people missing birthdays
  df = df[~df.birthday.isnull()]
  df["birthday"] = pd.to_datetime(df["birthday"])
  return df


def expand_df_dates(df):
  # Nice answer courtesy of https://stackoverflow.com/questions/43832484/expanding-a-dataframe-based-on-start-and-end-columns-speed
  dates = [pd.bdate_range(r[0], r[1], freq="A").to_series() 
      for r in df[['term_start', 'term_end']].values]

  lens = [len(x) for x in dates]

  df = pd.DataFrame(
          {col:np.repeat(df[col].values, lens) for col in df.columns}
      ).assign(date=np.concatenate(dates))
  return df


def create_df():
  """Create the dataframe of Congresspeople and their birthdays."""
  df = load_df_from_files()
  df = clean_df(df)
  df = expand_df_dates(df)
  df["age_at_t"] = ((df["date"] - df["birthday"]) / 365).dt.days  # Yeah, this is weird.

  return df


df = df[df["date"] <= "2018"]

pl.figure()
df.groupby("date").age_at_t.mean().plot()
pl.title("Average Age of Congress")


df.groupby(["date", "term_type"]).age_at_t.mean().unstack().plot()
pl.title("Average Age of Congress by House")
pl.ylabel("Average Age")
pl.savefig("time_avgage_byhouse.png")


df.groupby(["date", "gender"]).age_at_t.mean().unstack().plot()
pl.title("Average Age of Congress by Gender")
pl.ylabel("Average Age")
pl.savefig("time_avgage_bygender.png")


df[df.age_at_t > 0].groupby(["date"]).agg({"age_at_t": ["max", "min"]}).plot()
pl.title("Min/Max Age of Congress")
pl.ylabel("Age")
pl.savefig("time_minmaxage.png")


# Add in life expectancy
life = pd.read_csv("life_expectancy.csv")
life.Year = pd.to_datetime(life.Year.astype(str))

le = life[(life.Race == "All Races")
    & (life.Sex == "Both Sexes")]

le.columns = ["year", "race", "sex", "avg_life_exp", "death_rate"]

le.year = pd.to_datetime(le.year)

ax = df.groupby("date").age_at_t.mean().plot()
le.plot(x="year", y="avg_life_exp", ax=ax)

