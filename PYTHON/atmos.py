from scipy.io import FortranFile
import fortranformat as ff
from pandas.api.types import infer_dtype
import re

species_file = '../PHOTOCHEM/INPUTFILES/species.dat'

class Experiments:
    def __init__(self):
        self.models = []

    def add_model(self, model):
        pass

class AtmosPhotochem:
    def __init__(self, species):
        self.species = species

    def run(self):
        self.species.write_data()
        pass

    def get_output_data(self):
        pass

class Species:
    def __init__(self):
        self.species_file = '../PHOTOCHEM/INPUTFILES/species.dat'
        self. header_longlived = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL', 'lbound', 'vdep0',' fixedmr', 'sgflux', 'disth', 'mbound', 'smflux', 'veff0']
        self.header_shortlived = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL']
        self.header_inert = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL',
            'fixedmr']
        self.lines = self.read_lines()
        self.data = self.read_species_data()
        for key in self.data.keys():
            self.__dict__[key] = self.data[key]

    def read_lines(self):
        lines = []
        with open(self.species_file, mode='r') as f:
            for line in f.readlines():
                if line[0] != '*' and line:
                    if '!' in line:
                        line = line[:line.find('!')]
                    lines.append(line)
        return lines
    
    def read_species_data(self):
        species_data = {}
        for line in self.lines:
            line_data = line.split()

            if line_data[1] == 'LL':
                data = {k : v for k,v in zip(self.header_longlived, 
                    line_data[1:])}
            elif line_data[1] == 'IN':
                data = {k : v for k,v in zip(self.header_inert, 
                    line_data[1:])}
            else:
                 data = {k : v for k,v in zip(self.header_shortlived, 
                    line_data[1:])}

            data['format'] = self.get_format(line)
            species_data[line_data[0]] = data
        return species_data

    @staticmethod
    def get_format(line):
        items = re.split(r'(\s+)', line) 
        if items[-1] == '':
            items.pop(-1)
        lens = [len(item) for item in items] 
        lens = [sum(lens[i:i+2]) for i in range(0, len(lens), 2)] 
        fmat = '{:'+'}{:'.join([str(i) for i in lens]) + '}' 
        return fmat

    # TODO
    def write_data(self):
        pass

    




a = Species()
