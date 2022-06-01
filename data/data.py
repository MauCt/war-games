import csv
import enum
import json
import re
import numpy as np
import os

from fitter import Fitter, get_common_distributions, get_distributions

#from importlib_metadata import distribution
tens = dict(k=1e3, m=1e6, b=1e9)
regions_data = dict()

distributions_list = ['gamma', 'lognorm', "beta", "burr", "norm"]

class Region:
    def __init__(self, name):
        self.name = name
        self.territory = Variable('territory')
        self.population = Variable('population')
        self.growth_rate = Variable('growth_rate')
        self.income = Variable('income')
        self.literacy_rate = Variable('literacy_rate')
        self.military_spdng = Variable('military_spdng')

    def __str__(self):
        return json.dumps({
            'name': self.name,
            'territory': self.territory.to_json(),
            'population': self.population.to_json(),
            'growth_rate': self.growth_rate.to_json(),
            'income': self.income.to_json(),
            'literacy_rate': self.literacy_rate.to_json(),
            'military_spdng': self.military_spdng.to_json(),
        }, indent = 4)

class Variable:
    years = None # static list to be filled
    def __init__(self, name):
        self.name = name
        self.data = []
        self.distribution = ''
        self.mean = 0
        self.stdv = 0

    def to_json(self):
        return json.dumps({
            'name': self.name,
            'data': self.data,
            'distribution': self.distribution,
            'mean': self.mean,
            'stdv': self.stdv,
        })

def conversion(x):
    if x == '':
        return 0
    factor, exp = x[0:-1], x[-1].lower()
    if exp.isnumeric():
        return float(x)
    ans = int(float(factor) * tens[exp])
    return ans

script_dir = os.path.dirname(__file__)
def abs_path(rel_path):
    return os.path.join(script_dir, rel_path)

def get_regions():
    regions = dict()

    regions['europe'] = Region('Europe')
    regions['africa'] = Region('Africa')
    regions['asia'] = Region('Asia')
    regions['n_america'] = Region('N America')
    regions['s_america'] = Region('S America')
    regions['oceania_se_asia'] = Region('Oceania and S. E. Asia')
    regions['asia_middle_east'] = Region('Middle East Asia')

    with open(abs_path('src/world_region.csv'), mode='r', encoding="utf8") as inp:
        reader = csv.reader(inp)
        next(reader, None)
        for row in reader:
            country = row[1]
            region = row[2]
            if not region in regions_data:
                regions_data[region] = set()
            else:
                regions_data[region].add(country)
    
    def read_variable(filename, attr):
        with open(abs_path(f'src/{filename}.csv'), mode='r', encoding="utf8") as f:
            reader = csv.reader(f)
            years = [conversion(x) for x in next(reader)[1:]] # save years
            # e1.name -> getattr(e1,'name')
            getattr(regions[next(iter(regions))], attr).years = years # use arbitrary continent to save years
            for row in reader:
                country = row[0]
                for continent, countries in regions_data.items():
                    if country in countries:
                        new_row = row[1:]
                        converted = [conversion(x) for x in new_row]
                        data = getattr(regions[continent], attr).data

                        if not data:
                            getattr(regions[continent], attr).data = converted
                        else:
                            for i in range(len(data)):
                                getattr(regions[continent], attr).data[i] += int(converted[i])

    read_variable('population_total', 'population')

    with open(abs_path('src/surface_area_sq_km.csv'), mode='r', encoding="utf8") as ter:
        reader = csv.reader(ter)
        years = [conversion(x) for x in next(reader)[1:]] 
        regions[next(iter(regions))].population.years = years 
        for row in reader:
            country = row[0]
            for continent, countries in regions_data.items():
                if country in countries:
                    new_row = row[1:]
                    converted = [conversion(x) for x in new_row]

                    if not regions[continent].territory.data:
                        regions[continent].territory.data = converted
                    else:
                        for index, elem in enumerate(regions[continent].territory.data):
                            regions[continent].territory.data[index] += int(converted[index])

    #not sure if it has to be a sum :)
    with open(abs_path('src/population_growth_annual_percent.csv'), mode='r', encoding="utf8") as gro:
        reader = csv.reader(gro)
        years = [conversion(x) for x in next(reader)[1:]] 
        regions[next(iter(regions))].population.years = years
        for row in reader:
            country = row[0]
            for continent, countries in regions_data.items():
                if country in countries:
                    new_row = row[1:]
                    converted = [conversion(x) for x in new_row]

                    if not regions[continent].growth_rate.data:
                        regions[continent].growth_rate.data = converted
                    else:
                        for index, elem in enumerate(regions[continent].growth_rate.data):
                            regions[continent].growth_rate.data[index] += int(converted[index])

    with open(abs_path('src/income_per_person_gdppercapita_ppp_inflation_adjusted.csv'), mode='r', encoding="utf8") as inc:
        reader = csv.reader(inc)
        years = [conversion(x) for x in next(reader)[1:]] 
        regions[next(iter(regions))].population.years = years
        for row in reader:
            country = row[0]
            for continent, countries in regions_data.items():
                if country in countries:
                    new_row = row[1:]
                    converted = [conversion(x) for x in new_row]

                    if not regions[continent].income.data:
                        regions[continent].income.data = converted
                    else:
                        for index, elem in enumerate(regions[continent].income.data):
                            regions[continent].income.data[index] += int(converted[index])

    with open(abs_path('src/ms_mil_xpnd_gd_zs.csv'), mode='r', encoding="utf8") as mil:
        reader = csv.reader(mil)
        years = [conversion(x) for x in next(reader)[1:]] 
        regions[next(iter(regions))].population.years = years
        for row in reader:
            country = row[0]
            for continent, countries in regions_data.items():
                if country in countries:
                    new_row = row[1:]
                    converted = [conversion(x) for x in new_row]

                    if not regions[continent].military_spdng.data:
                        regions[continent].military_spdng.data = converted
                    else:
                        for index, elem in enumerate(regions[continent].military_spdng.data):
                            regions[continent].military_spdng.data[index] += int(converted[index])

    literacy_cnt = dict()
    with open(abs_path('src/literacy_rate_adult_total_percent_of_people_ages_15_and_above.csv'), mode='r', encoding="utf8") as lit:
        reader = csv.reader(lit)
        years = [conversion(x) for x in next(reader)[1:]] 
        regions[next(iter(regions))].population.years = years
        for row in reader:
            country = row[0]
            for continent, countries in regions_data.items():
                if country in countries:
                    new_row = row[1:]
                    converted = [conversion(x) for x in new_row]

                    if not continent in literacy_cnt:
                        literacy_cnt[continent] = [0 for x in range(len(converted))] # counter initialization

                    if not regions[continent].literacy_rate.data:
                        regions[continent].literacy_rate.data = converted
                    else:
                        for index, elem in enumerate(regions[continent].literacy_rate.data):
                            regions[continent].literacy_rate.data[index] += int(converted[index])
                    
                    for index, x in enumerate(converted):
                        if x != 0: 
                            literacy_cnt[continent][index] += 1 # counter
    
        for continent, cnt_list in literacy_cnt.items():
            for index in range(len(regions[continent].literacy_rate.data)):
                counter = cnt_list[index]
                if counter > 0:
                    regions[continent].literacy_rate.data[index] /= counter

    #Calculating means, stdv's and best fit distribution :)
    for continent, region in regions.items():
        region.population.mean = np.mean(region.population.data)
        region.population.stdv = np.std(region.population.data)
        f = Fitter(np.array(region.population.data),distributions=distributions_list)
        f.fit()
        region.population.distribution = f.get_best(method = 'sumsquare_error')

        region.territory.mean = np.mean(region.territory.data)
        region.territory.stdv = np.std(region.territory.data)
        f = Fitter(np.array(region.territory.data), distributions=distributions_list)
        f.fit()
        region.territory.distribution = f.get_best(method = 'sumsquare_error')

        region.growth_rate.mean = np.mean(region.growth_rate.data)
        region.growth_rate.stdv = np.std(region.growth_rate.data)
        f = Fitter(np.array(region.growth_rate.data), distributions=distributions_list)
        f.fit()
        region.growth_rate.distribution = f.get_best(method = 'sumsquare_error')

        region.income.mean = np.mean(region.income.data)
        region.income.stdv = np.std(region.income.data)
        f = Fitter(np.array(region.income.data), distributions=distributions_list)
        f.fit()
        region.income.distribution = f.get_best(method = 'sumsquare_error')

        region.military_spdng.mean = np.mean(region.military_spdng.data)
        region.military_spdng.stdv = np.std(region.military_spdng.data)
        f = Fitter(np.array(region.military_spdng.data), distributions=distributions_list)
        f.fit()
        region.military_spdng.distribution = f.get_best(method = 'sumsquare_error')

    return regions


regions = get_regions()
for name, reg in regions.items():
    print(reg)