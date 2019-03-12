import json

import matplotlib.style as style
import numpy as np
import pandas as pd
import pylab as pl


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
  """Create a DataFrame where each row contains information on a 
  Congressperson's age on December 31st for each year in which he or she is in 
  office.
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
  """Expand the dataframe so that each row has the age of a Congressperson in a
  particular year.
  
  This code based on: 
  https://stackoverflow.com/questions/43832484/expanding-a-dataframe-based-on-start-and-end-columns-speed
  """
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


# Load that data
df = create_df()


# Limit to when next term ends (as of time of writing, 2019-03-09)
df = df[df["date"] <= "2020-12-31"]


# Set the style
style.use("seaborn-whitegrid")


# Overall average age
df.groupby("date").age_at_t.mean().plot(figsize=(8, 4))
pl.title("Average Age of Congress")
pl.ylabel("Average Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_avgage.png")


# Mean and Median
tmp = df.groupby("date").agg({"age_at_t": ["mean", "median"]}).plot()
pl.title("Average and Median Age of Congress")


# Age by Senate vs. House
tmp = (df
  .groupby(["date", "term_type"])
  .age_at_t
  .mean()
  .unstack())
tmp.columns = ["House", "Senate"]
tmp.plot(figsize=(8, 4))
pl.title("Average Age of Congress by House")
pl.ylabel("Average Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_avgage_byhouse.png")


# Age by Gender
(df
  .groupby(["date", "gender"])
  .age_at_t
  .mean()
  .unstack()
  .plot(figsize=(8, 4)))
pl.title("Average Age of Congress by Gender")
pl.ylabel("Average Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_avgage_bygender.png")


# Min and Max Age
# df[df.age_at_t > 0].groupby(["date"]).agg({"age_at_t": ["max", "min"]}).plot(figsize=(8, 4))
tmp = (df
  .groupby(["date"])
  .agg({"age_at_t": ["max", "min"]})
  .plot(figsize=(8, 4)))
tmp.columns = ["Min", "Max"]
pl.title("Min and Max Age of Congress")
pl.ylabel("Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_minmaxage.png")


tmp = (df[df.date >= "1900"]
  .groupby(["date"])
  .agg({"age_at_t": ["max", "min"]})
  .plot(figsize=(8, 4)))
tmp.columns = ["Min", "Max"]
pl.title("Min and Max Age of Congress")
pl.ylabel("Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_minmaxage_filtered.png")


# Age by Party
# Yeah this doesn't look very good.
(df
  .groupby(["date", "party"])
  .age_at_t
  .mean()
  .unstack()
  .plot())
pl.title("Average Age of Congress by Party")
pl.ylabel("Average Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_avgage_byparty_all.png")


# Age by Dem v Rep
(df[df.party.isin(["Democrat", "Republican", "Independent"])]
  .groupby(["date", "party"])
  .age_at_t
  .mean()
  .unstack()
  .plot())
pl.title("Average Age of Congress by (some) Party")
pl.ylabel("Average Age")
pl.xlabel("Date")
pl.tight_layout()
pl.savefig("fig/time_avgage_byparty_some.png")
