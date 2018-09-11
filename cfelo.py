#!/usr/bin/env python3
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Original MultiplayerELO Class from: https://github.com/FigBug/Multiplayer-ELO
# Made some minor fixes


class ELOPlayer:
    name = ""
    place = 0
    eloPre = 0
    eloPost = 0
    eloChange = 0


class ELOMatch:
    def __init__(self):
        self.players = []

    def addPlayer(self, name, place, elo):
        player = ELOPlayer()

        player.name = name
        player.place = int(place)
        player.eloPre = int(elo)

        self.players.append(player)
        # print('Added:', player.name, player.place, player.eloPre)

    def getELO(self, name):
        for p in self.players:
            if p.name == name:
                return p.eloPost
        print(p.name, 'name not found. Default ELO: 1500')
        return 1500

    def getELOChange(self, name):
        for p in self.players:
            if p.name == name:
                return p.eloChange

        return 0

    def calculateELOs(self):
        n = len(self.players)
        K = (n / (n - 1)) + 1
        print('players:', n, 'K:', K)

        for i in range(n):
            curPlace = self.players[i].place
            curELO = self.players[i].eloPre

            for j in range(n):
                if i != j:
                    opponentPlace = self.players[j].place
                    opponentELO = self.players[j].eloPre

                    # work out S
                    if curPlace < opponentPlace:
                        S = 1.0
                    elif curPlace == opponentPlace:
                        S = 0.5
                    else:
                        S = 0.0

                    # work out EA
                    EA = 1 / \
                        (1.0 + math.pow(10.0, (opponentELO - curELO) / 400.0))

                    # calculate ELO change vs this one opponent, add it to our change bucket
                    # I currently round at this point, this keeps rounding changes symetrical between EA and EB, but changes K more than it should
                    self.players[i].eloChange += round(K * (S - EA))

            # add accumulated change to initial ELO for final ELO
            self.players[i].eloPost = self.players[i].eloPre + \
                self.players[i].eloChange


def processdata(df, workouts):
    event = []

    for i, w in enumerate(workouts):
        df[w + '_ELO'] = 0

        # Create a "match" for each event
        event.append(ELOMatch())

        # Iterate on each row to add the players (apply didn't work right?)
        for index, row in df.iterrows():
            # If the player placed then add the player to this match
            # Check for NaN - there has to be a better python way?...
            if (row[workouts[i]] == row[workouts[i]]):
                event[i].addPlayer(row['NAME'], row[workouts[i]], row['ELO'])

        event[i].calculateELOs()

        # Get the data from each event and store it
        # Also update each players current ELO
        # Use apply instead of itterate.
        # Per spec: You should never modify something you are iterating over.
        # This is not guaranteed to work in all cases
        # NOTE THIS DOESN'T WORK IF A PLAYER DROPS OUT.
        # It does an apply for all NAMES
        df[w + '_ELO'] = df.apply(lambda x: event[i].getELO(x['NAME']), axis=1)
        df['ELO'] = df[w + '_ELO']
    return df


def cleanregionaldata(df, renamecomlums):
    # clean up the column name cells
    df.columns = renamecolumns

    # Make Name a single long name
    df['NAME'] = df['NAME'].str.replace('-', '')
    df['NAME'] = df['NAME'].str.replace('.', '')
    df['NAME'] = df['NAME'].str.replace(' ', '')

    # Use regex to get the name only
    df['NAME'] = df['NAME'].str.extract(r'^(\w+)', expand=False)

    # Use regex to get the first number (place) from the workout cell,
    # make it into a number or a NaN
    for w in workouts:
        df[w] = df[w].str.extract(r'^(\d+)', expand=False)
        df[w] = df[w].apply(pd.to_numeric, errors='coerce')
    return df


#
# Calculate 2018 Open ELO
#
df = pd.read_csv('./2018_open_top1200.csv',)
print(df.head())
print(df.info())

workouts = ['18.1', '18.2', '18.2A', '18.3', '18.4', '18.5']
renamecolumns = ['RANK', 'NAME', 'POINTS'] + workouts
workouts_elo = [x + '_ELO' for x in workouts]

# Clean the 2018 Open Data
# clean up the column name cells
df.columns = renamecolumns

# Make Name a single long name
df['NAME'] = df['NAME'].str.replace('ACCEPTED', '')
df['NAME'] = df['NAME'].str.replace('TEAM', '')
df['NAME'] = df['NAME'].str.replace('-', '')
df['NAME'] = df['NAME'].str.replace('.', '')
df['NAME'] = df['NAME'].str.replace(' ', '')

# Use regex to get the name only
df['NAME'] = df['NAME'].str.extract(r'^(\w+)', expand=False)

# Use regex to get the first number (place) from the workout cell,
# make it into a number or a NaN
for w in workouts:
    df[w] = df[w].str.extract(r'^(\d+)', expand=False)
    df[w] = df[w].apply(pd.to_numeric, errors='coerce')

# Everyon starts with an ELO of 1500
df['ELO'] = 1500
print(df.head())

# Calculate the ELOs
df = processdata(df, workouts)

# Save the results
df.to_csv('./cf_open_elo_results.csv')

# Get the ELOs to seed the next round
dfopen = df[['NAME', 'ELO']]
print(dfopen.head())


#
# Calculate 2018 Regionals ELO
#
regionalfilenames = ['atlantic', 'meridian', 'central', 'pacific', 'east',
                     'south', 'europe', 'west', 'latinamerica']
regionalresults = []

for file in regionalfilenames:
    df = pd.read_csv('./2018_men_' + file + '_region.csv',)
    print(df.head())
    print(df.info())

    workouts = ['EVENT 1', 'EVENT 2', 'EVENT 3', 'EVENT 4', 'EVENT 5', 'EVENT 6']
    renamecolumns = ['RANK', 'NAME', 'POINTS'] + workouts
    workouts_elo = [x + '_ELO' for x in workouts]

    # Clean the 2018 Regionals Data
    cleanregionaldata(df, renamecolumns)

    # Use the open ELO
    df = pd.merge(df, dfopen, on='NAME')
    df['ELO_IN'] = df['ELO']
    print(df.head())

    # Calculate the ELOs
    df = processdata(df, workouts)

    # Save the results
    df.to_csv('./cf_' + file + '_regional_results.csv')

    # Get the ELOs to seed the next round
    df1 = df[['NAME', 'ELO']]
    regionalresults.append(df1)
    print(df1.head())

print(type(regionalresults))
print(type(regionalresults[0]))
print(len(regionalresults))
#
# Crossfit 2018 Games ELO
#
df = pd.read_csv('./2018_men_leaderboard.csv',)

print(df.head())
print(df.info())

workouts = ['CRIT', '30 MUSCLE-UPS',
            'CROSSFIT TOTAL', 'MARATHON ROW', 'THE BATTLEGROUND',
            'CLEAN & JERK SPEED LADDER', 'FIBONACCI',
            'MADISON TRIPLUS', 'CHAOS', 'BICOUPLET 2',
            'BICOUPLET 1', 'TWO-STROKE PULL', 'HANDSTAND WALK',
            'AENEAS']
renamecolumns = ['RANK', 'NAME', 'POINTS'] + workouts
workouts_elo = [x + '_ELO' for x in workouts]

# clean up the column name cells
df.columns = renamecolumns

# Make Name a single long first name
df['NAME'] = df['NAME'].str.replace(' ', '')

# Cleanup the NAME cells. Get everything on the same line
df['NAME'] = df['NAME'].str.replace('\n', ' ')

# remove hyphen
df['NAME'] = df['NAME'].str.replace('-', '')

# Use regex to get the first and last name only
df['NAME'] = df['NAME'].str.extract(r'^(\w+\s\w+)', expand=False)

# Make Name a single long name
df['NAME'] = df['NAME'].str.replace(' ', '')

# Use regex to get the first number (place) from the workout cell,
# make it into a number or a NaN
for w in workouts:
    df[w] = df[w].str.extract(r'^(\d+)', expand=False)
    df[w] = df[w].apply(pd.to_numeric, errors='coerce')

df['ELO'] = np.nan

# Everyone starts with an ELO from the open
for result in regionalresults:
    df = pd.merge(df, result, on='NAME', how='left')
    df['ELO_x'] = df['ELO_x'].fillna(df['ELO_y'])
    df['ELO'] = df['ELO_x']
    df = df.drop(columns=['ELO_x', 'ELO_y'])

# TODO stop on NaN ELOs!
print(df[df.isnull().any(axis=1)]['ELO'].head())

# Save the incoming ELOs
df['ELO_IN'] = df['ELO']
print(df.head())

# Calculate the ELOs
df = processdata(df, workouts)

# Save the dataframe to a file
df.to_csv('./cf_elo_results.csv')


#
# Plot the data
#
# plt.show()
