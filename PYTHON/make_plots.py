import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

PHOTOCHEM_OUTPUT = '../PHOTOCHEM/OUTPUT/profile.pt'
CLIMATE_OUTPUT= '../CLIMA/IO/clima_last.tab'

#Get columns from first line of photochem output
with open(PHOTOCHEM_OUTPUT, 'r') as f:
    photo_columns = f.readline()
photo_columns = [col.strip() for col in photo_columns.split('     ')][1:]

#Get columns from first line of climate output
with open(CLIMATE_OUTPUT, 'r') as f:
    climate_columns = f.readline()
climate_columns = [col.strip() for col in climate_columns.split('    ')
    if col.strip() != '']

#read and clean photochem data
photochem_data = pd.read_csv(PHOTOCHEM_OUTPUT,
    skiprows=1, delimiter=' ', header=None)
photochem_data.drop(columns=[0, 1], inplace=True)
photochem_data.columns = photo_columns

#read and clean clima data
climate_data = pd.read_csv(CLIMATE_OUTPUT,
    skiprows=1, delimiter='   ', header=None)
first_columns = pd.DataFrame(climate_data[0].str.split(' ').values.tolist(),
    dtype=float)[[0,2,3]]
first_columns.columns = climate_columns[:3]
climate_data.drop(columns=0, inplace=True)
climate_data.columns = climate_columns[3:]
climate_data = first_columns.join(climate_data)


#make photochem plots
fig, axs = plt.subplots(5,3, figsize= (17,21))
axs =  axs.flatten()
for i in range(0,15):
    plt.sca(axs[i])
    plt.plot(photochem_data[photo_columns[i+1]], photochem_data['Alt'],'k')
    plt.xlabel(photo_columns[i+1])
    plt.ylabel('Altitude')
fig.savefig('photochem_plots.jpg')

#make climate plots
fig1, axs = plt.subplots(3,3, figsize= (17,15))
axs =  axs.flatten()
for i in range(0,8):
    plt.sca(axs[i])
    plt.plot(climate_data[climate_columns[i+1]], climate_data['ALT'],'k')
    plt.xlabel(climate_columns[i+1])
    plt.ylabel('Altitude')
fig1.savefig('climate_plots.jpg')
