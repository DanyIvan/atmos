from tempfile import mkstemp
from shutil import move, copymode, copy
from os import fdopen, remove
from ast import literal_eval
import subprocess
import pandas as pd
import pickle
import re
import os

class Experiments:
    def __init__(self):
        self.models = []

    def add_model(self, model):
        self.models.append(model)

class AtmosPhotochem:
    def __init__(self):
        self.temp_path='../PHOTOCHEM/INPUTFILES/TEMPLATES/'
        self.photochem_templates = ['Archean+haze', 'ArcheanSORG+haze',
            'MarsModern+Cl',  'ModernEarth',  'ModernEarth+Cl']
        self.input_filenames = ['in.dist', 'input_photchem.dat','reactions.rx',
            'parameters.inc', 'species.dat', 'PLANET.dat']
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.clean_command = ['make', '-f', 'PhotoMake', 'clean']
        self.make_command = ['make', '-f', 'PhotoMake']
        self.run_command = [self.dir_path + '/../Photo.run']
        self.species = Species()
        self.output = None
    
    def run(self, template, recompile=True):
        self.set_template(template)
        self.species.write_data()
        os.chdir('../')
        if recompile:
            self._run_command(self.clean_command)
            self._run_command(self.make_command)
        self._run_command(self.run_command)
        os.chdir(self.dir_path)
        self.output = Output()

    def set_template(self, template):
        if template not in self.photochem_templates:
            raise NameError('Template not found')
        folder = self.temp_path + template + '/'
        os.chdir(folder)
        for file in self.input_filenames:
            if file == 'in.dist':
                copy(file, "../../..")
            else:
                copy(file, "../..")
            print(f'Copied {file} from {os.getcwd()}')
        os.chdir(self.dir_path)
    
    def set_species(self, species):
        self.species = Species()

    def set_output(self, output):
        self.output = Output()

    @staticmethod
    def _run_command(command): 
        process = subprocess.Popen(command, stdout=subprocess.PIPE) 
        while True: 
            output = process.stdout.readline() 
            if output == b'' and process.poll() is not None: 
                break 
            if output: 
                print(output.strip()) 

class Output():
    def __init__(self):
        self.output_path = '../PHOTOCHEM/OUTPUT/'
        self.output_profile_path = self.output_path + 'profile.pt'
        self.output_mixrat_path = self.output_path + 'PTZ_mixingratios_out.dist'
        self.profile = self.get_output_data(self.output_profile_path)
        self.mixrat = self.get_output_data(self.output_mixrat_path)

    @staticmethod
    def get_output_data(file):
        data = []
        with open(file) as f:
            for idx, line in enumerate(f.readlines()):
                if idx == 0:
                    header = line.split()
                else:
                    row = [eval(s) for s in line.split()]
                    data.append(row)
            return pd.DataFrame(data, columns=header)
    

class Species_Dict(object):
    def __init__(self, adict):
        self.__dict__.update(adict)
    def __repr__(self):
        return dict.__repr__(self.__dict__)

class Species:
    def __init__(self):
        self.species_file = '../PHOTOCHEM/INPUTFILES/species.dat'
        self. header_longlived = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL', 'lbound', 'vdep0','fixedmr', 'sgflux', 'disth', 'mbound', 'smflux', 'veff0']
        self.header_shortlived = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL']
        self.header_inert = ['long_lived', 'O', 'H', 'C', 'S', 'N', 'CL',
            'fixedmr']
        self.lines = self.read_lines()
        self.data = self.read_species_data()
        for key in self.data.keys():
            self.__dict__[key] = Species_Dict(self.data[key])

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

    def write_data(self):
        fh, abs_path = mkstemp()
        with fdopen(fh,'w') as new_file:
            with open(self.species_file) as old_file:
                for line in old_file:
                    if line[0] != '*' and line:
                        key = line.split()[0] 
                        vals = list(self.__dict__[key].__dict__.values())
                        fmat = vals[-1]
                        vals.pop(-1)
                        vals.insert(0, key)
                        line = fmat.format(*vals) + '\n'
                        new_file.write(line)
                    else:
                        new_file.write(line)
        #Copy the file permissions from the old file to the new file
        copymode(self.species_file, abs_path)
        #Remove original file
        remove(self.species_file)
        #Move new file
        move(abs_path, self.species_file)



model = AtmosPhotochem()
# model.run('ModernEarth')


