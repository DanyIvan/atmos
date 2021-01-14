from tempfile import mkstemp
from shutil import move, copymode, copy
from os import fdopen, remove
import plotly.express as px 
import subprocess
import pandas as pd
import pickle
import re
import os

class Experiments:
    '''
    The Experiments class stores model runs

    Attributes
    -----------
    models (list): list of model runs
    '''
    def __init__(self):
        self.models = []
        self.variant = None

    def run_all(self, template):
        '''Runs all the models in the models list'''
        for model in self.models:
            model.run(template)
    
    def set_variant(self, variant):
        self.variant = variant

    def animate(self, output, variant, name):
        '''Makes a plotly animation of the output of an experiment
        
        Parameters
        ----------
        output (string): one of 'profile' or 'mixrat'
        variant (list): list of values that a species takes trhought the
        different model runs. Example variats for oxygen ['0.21', '0.20']
        name (string): name of the variant: Example: 'O2'
        '''
        if len(self.models) < 2:
            raise Exception('Experiments object must have at lest 2 models')
        data = []
        for idx, model in enumerate(self.models):
            df = model.output.__dict__[output].melt(id_vars='ALT',
            var_name='var', value_name='value')
            df[name] = variant[idx]
            data.append(df)
        data = pd.concat(data)
        fig = px.line(data, x="value", y="ALT", color='var',
            animation_frame=name) 
        fig.show()


class AtmosPhotochem:
    ''' 
    The AtmosPhotochem class has all attributes and method necessary for running,
        modifying and reading the output of the atmos photochem model

    Attributes
    ----------
    temp_path(string): path of photochem template files
    photochem_templates(list): names of currently available templates
    input_filenames(list): names of inputfiles for running the model
    dir_path(string): path of this file location
    clean_command(list): command to run make clean
    make_command(list): command to compile model
    run_command(list): command to run model
    species (class): class containing information about the model input for
        chemical species
    output(class): contains the output data of the model run
    '''
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
        '''Runs the model
        
        Parameters
        ----------
        template(string): template to run
        recompile(bool): recompiles the model if true
        '''
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
        '''Sets the data of a template for a model run
        
        Parameters
        ---------
        template(string): templete to set
        '''
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
    
    def set_species(self):
        '''Sets species data'''
        self.species = Species()

    def set_output(self):
        '''Sets output data'''
        self.output = Output()

    def plot_output(self, output):
        '''Plots output data
        
        Parameters
        ----------
        output (DataFrame): contains the output data
        '''
        melt_output = output.melt(id_vars='ALT', var_name='var',
             value_name='value') 
        fig = px.line(melt_output, x="value", y="ALT", color='var') 
        fig.show()

    @staticmethod
    def _run_command(command): 
        '''Runs a command retrieving output:
        
        Parameters
        ---------
        command(list): constains the command to run
        '''
        process = subprocess.Popen(command, stdout=subprocess.PIPE) 
        while True: 
            output = process.stdout.readline() 
            if output == b'' and process.poll() is not None: 
                break 
            if output: 
                print(output.strip()) 

class Output():
    '''
    This class stores reads and stores a model output data

    Attributes
    ---------
    output_path (string): path of photochem model output
    output_profile_path (string): path of ptofile output data file
    output_mixrat_path (string): path of mixing ratios output data file
    profile (DataFrame): contains profile output data
    mixrat (DataFrame): contains mixing ratios output data
    '''
    def __init__(self):
        self.output_path = '../PHOTOCHEM/OUTPUT/'
        self.output_profile_path = self.output_path + 'profile.pt'
        self.output_mixrat_path = self.output_path + 'PTZ_mixingratios_out.dist'
        self.profile = self.get_output_data(self.output_profile_path)
        self.mixrat = self.get_output_data(self.output_mixrat_path)

    @staticmethod
    def get_output_data(file):
        '''Reads data from an output file
        
        Parameters
        ---------
        file (string): path of file to read

        Retuns
        ------
        df (DataFrame): dataframe of output data
        '''
        data = []
        with open(file) as f:
            for idx, line in enumerate(f.readlines()):
                if idx == 0:
                    header = line.split()
                else:
                    row = [eval(s) for s in line.split()]
                    data.append(row)
            df = pd.DataFrame(data, columns=header)
            df.columns = [col.upper() for col in df.columns]
            return df
    

class Species_Dict(object):
    ''' This class stores specific species data'''
    def __init__(self, adict):
        self.__dict__.update(adict)
    def __repr__(self):
        return dict.__repr__(self.__dict__)

class Species:
    ''' This class stores all the data of chemical species for a model

    Attributes
    ---------
    species_file (string): path of species input data
    header_longlived (list): contains varnames of longlived chemcial species
    header_shortlived (list): contains varnames of shortlived chemcial species
    header_inert (list): contains varnames of inert chemcial species
    lines(list): contains the lines of species datafile
    data(dict): contains data for each species
    Each of the chemical species of a model run is also an attribute of this 
        class
    '''
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
        '''Reads lines of species datafile
        
        Returns
        -------
        lines(list): contains the lines of species datafile
        '''
        lines = []
        with open(self.species_file, mode='r') as f:
            for line in f.readlines():
                if line[0] != '*' and line:
                    if '!' in line:
                        line = line[:line.find('!')]
                    lines.append(line)
        return lines
    
    def read_species_data(self):
        '''Reads data of species datafile
        
        Returns
        ------
        species_data(dict): contains the data for each species
        '''
        species_data = {}
        for line in self.lines:
            line_data = line.split()

            if line_data[1] == 'LL':
                data = {k : v for k,v in zip(
                    self.header_longlived[:len(line_data[1:])],line_data[1:])}
            elif line_data[1] == 'IN':
                header = self.header_inert if len(line_data[1:]) == len(
                    self.header_inert) else self.header_longlived
                data = {k : v for k,v in zip(header[:len(line_data[1:])],
                    line_data[1:])}
            else:
                header = self.header_shortlived if len(line_data[1:]) == len(
                    self.header_shortlived) else self.header_longlived
                data = {k : v for k,v in zip(header[:len(line_data[1:])],
                    line_data[1:])}

            data['format'] = self.get_format(line)
            species_data[line_data[0]] = data
        return species_data

    @staticmethod
    def get_format(line):
        '''Gets formar of a line
        
        Parameters
        ----------
        line(string): the line whose format is to be calculated

        Returns
        -------
        fmat(string): format of line
        '''
        items = re.split(r'(\s+)', line) 
        if items[-1] == '':
            items.pop(-1)
        lens = [len(item) for item in items] 
        lens = [sum(lens[i:i+2]) for i in range(0, len(lens), 2)] 
        fmat = '{:'+'}{:'.join([str(i) for i in lens]) + '}' 
        return fmat

    def write_data(self):
        '''Writes data from a Species object to a species datafile'''
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

def save_object(object, filename):
    with open(filename, 'wb') as f:
        pickle.dump(object, f)

def load_object(path):
    with open(path, 'rb') as f:
        object = pickle.load(f)
    return object

model = AtmosPhotochem()
# model.run('ModernEarth')


