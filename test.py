from termcolor import colored
from tqdm import tqdm
from glob import glob
import subprocess as sp
import random
import sys
import os
import re

TEST_GRAPHS = [
    'FullGraph',
    'WorstCase',
    'SparseGraph',
    'ScaleFree',
    'RDF',
]

TEST_TYPES = [
    'Construct',
    'Deconstruct',
]

def log(s):
    print(colored(s, 'green'))


def filename(path):
    return os.path.splitext(os.path.basename(path))[0]


def filesize(path):
    return int(sp.run(f'wc -l {path}', capture_output=True, shell=True).stdout.split()[0].decode('utf-8'))


def init(tests):
    log('Start building executables...')
    sp.run('make JOBS=32', shell=True)
    log('Finish building executables...')

    if os.path.exists('input') is False:
        log('Created input directory')
        os.mkdir('input')

    if os.path.exists('results') is False:
        log('Created results directory')
        os.mkdir('results')

    if os.path.exists('Empty.txt') is False:
        sp.run('touch Empty.txt', shell=True)
    
    for test in tests:
        if os.path.exists(f'input/{test}') is False:
            os.mkdir(f'input/{test}')
            log(f'Created input/{test} directory')

            os.mkdir(f'input/{test}/Graphs')
            log(f'Created input/{test}/Graphs directory')

            os.mkdir(f'input/{test}/Grammars')
            log(f'Created input/{test}/Grammars directory')

            os.mkdir(f'input/{test}/Queries')
            log(f'Created input/{test}/Queries directory')
            
    pwd = os.path.abspath('.')
    
    if os.path.exists('deps/CFPQ_Data/data/FullGraph/Matrices') is False:
        log('Start initialize CFPQ_Data...')
        sp.run('git clone https://github.com/viabzalov/CFPQ_Data.git deps/CFPQ_Data', shell=True)
        sp.run(f'pip3 install -r requirements.txt', cwd=f'{pwd}/deps/CFPQ_Data',shell=True)
        sp.run(f'python3 init.py', cwd=f'{pwd}/deps/CFPQ_Data', shell=True)
        log('Finish initialize CFPQ_Data...')

    for test in tests:
        graphs = os.listdir(f'deps/CFPQ_Data/data/{test}/Matrices')
        for g in tqdm(graphs):
            if filesize(f'deps/CFPQ_Data/data/{test}/Matrices/{g}') <= int(75000):
                g_txt = re.sub('(.*)(\.(xml|owl|rdf))', '\g<1>.txt', g)
                if os.path.exists(f'input/{test}/Graphs/{g_txt}') is False:
                    log(f'Start adding graph {g} to input...')
                    sp.run(f'python3 deps/CFPQ_Data/tools/RDF_to_triple/converter.py deps/CFPQ_Data/data/{test}/Matrices/{g} deps/CFPQ_Data/data/{test}/convconfig', shell=True)
                    sp.run(f'mv deps/CFPQ_Data/data/{test}/Matrices/{g_txt} input/{test}/Graphs/{g_txt}', shell=True)
                    log(f'Finish adding graph {g} to input...')

                if 'Construct' in TEST_TYPES:
                    construct_graph_queries(test, g_txt)
                if 'Deconstruct' in TEST_TYPES:
                    deconstruct_graph_queries(test, g_txt)
                if 'Correctness' in TEST_TYPES:
                    correctness_graph_queries(test, g_txt)
        
        grammars = os.listdir(f'deps/CFPQ_Data/data/{test}/Grammars')
        for gr in tqdm(grammars):
            gr_cnf = re.sub('(.*)(\.txt)', '\g<1>_cnf.txt', gr)
            if os.path.exists(f'input/{test}/Grammars/{gr_cnf}') is False:
                log(f'Start adding grammar {gr_cnf} to input...')
                sp.run(f'python3 deps/CFPQ_Data/tools/grammar_to_cnf/grammar_to_cnf.py deps/CFPQ_Data/data/{test}/Grammars/{gr} -o input/{test}/Grammars/{gr_cnf}', shell=True)
                log(f'Finish adding grammar {gr_cnf} to input...')


def construct_graph_queries(test, graph):
    q_dir = f'input/{test}/Queries/{filename(graph)}/Construct/'
    if os.path.exists(q_dir) is False:
        os.makedirs(q_dir, exist_ok=True)    
    for type in ['brute', 'smart']:
        with open(f'input/{test}/Graphs/{graph}', 'r') as fin:
            q_path = q_dir + f'{type}.txt'
            with open(q_path, 'w') as fout:
                log(f'Start adding queries to {q_path}...')
                for line in tqdm(fin):
                    v, edge, to = line.split()
                    fout.write(f'{type}-edge-add {v} {to} {edge}\n')
                log(f'Finish adding queries to {q_path}...')


def deconstruct_graph_queries(test, graph):
    q_dir = f'input/{test}/Queries/{filename(graph)}/Deconstruct/'
    if os.path.exists(q_dir) is False:
        os.makedirs(q_dir, exist_ok=True)
    for type in ['brute', 'smart']:
        with open(f'input/{test}/Graphs/{graph}', 'r') as fin:
            q_path = q_dir + f'{type}.txt'
            with open(q_path, 'w') as fout:
                log(f'Start adding queries to {q_path}...')
                for line in tqdm(fin):
                    v, edge, to = line.split()
                    fout.write(f'{type}-edge-delete {v} {to} {edge}\n')
                log(f'Finish adding queries to {q_path}...')


def correctness_graph_queries(test, graph):
    q_dir = f'input/{test}/Queries/{filename(graph)}/Correctness/'
    if os.path.exists(q_dir) is False:
        os.makedirs(q_dir, exist_ok=True)

    min_v = int(10**18)
    max_v = -int(10**18)
    with open(f'input/{test}/Graphs/{graph}', 'r') as fin:
        for line in fin:
            v, edge, to = line.split()
            min_v = min(list(map(int, [v, to, min_v])))
            max_v = max(list(map(int, [v, to, max_v])))
    
    for type in ['brute', 'smart']:
        with open(f'input/{test}/Graphs/{graph}', 'r') as fin:
            q_path = q_dir + f'{type}.txt'
            with open(q_path, 'w') as fout:
                log(f'Start adding queries to {q_path}...')
                for line in tqdm(fin):
                    v, edge, to = line.split()
                    fout.write(f'{type}-edge-delete {v} {to} {edge}\n')
                    for i in range(min_v, max_v + 1):
                        for j in range(i + 1, max_v + 1):
                            fout.write(f'find-path {i} {j}\n')
                log(f'Finish adding queries to {q_path}...')


def test_one_graph(test, graph, grammar, queries):
    g_name = filename(graph)
    gr_name = filename(grammar)
    q_name = filename(queries)
    
    if os.path.exists(test) is False:
        os.makedirs(test, exist_ok=True)

    results_path = f'{test}/{g_name}_{gr_name}_{q_name}'

    log(f'Start testign Graph: {g_name} with Grammar: {gr_name} and Queries: {q_name}...')
    
    sp.run(f'./main {graph} {grammar} {queries} > {results_path}', shell=True)

    time = None
    multiplications = 0
    flag = False
    with open(results_path, 'r') as fin:
        for line in fin:
            if flag is False:
                flag = True
                continue
            if re.fullmatch('(Total time:) (.*) s\n', line) is not None:
                time = re.sub('(Total time:) (.*) s\n', '\g<2>', line)
            if re.fullmatch('(Iteration count:) (.*)\n', line) is not None:
                tmp = re.sub('(Iteration count:) (.*)\n', '\g<2>', line)
                multiplications += int(tmp)

    log(f'Total time: {time} s')

    log(f'Finish testign Graph: {g_name} with Grammar: {gr_name} and Queries: {q_name}...')

    return (time, multiplications)


def test_one_delete(test, graph, grammar):
    g_name = filename(graph)
    gr_name = filename(grammar)

    results_path = f'{g_name}_{gr_name}_tmp.txt'

    log(f'Start testign Graph: {g_name} with Grammar: {gr_name}...')

    results = {}

    for type in ['brute', 'smart']:
        cnt = 0
        sum = 0
        flag = False
        with open(f'input/{test}/Graphs/{g_name}.txt', 'r') as fin:
            for line in fin:
                v, edge, to = line.split()
                sp.run(f'echo {type}-edge-delete {v} {to} {edge} > tmp.txt', shell=True)
                sp.run(f'./main {graph} {grammar} tmp.txt > {results_path}', shell=True)

                with open(results_path, 'r') as ffin:
                    for lline in ffin:
                        if flag is False:
                            flag = True
                            continue
                        if re.fullmatch('(Total time:) (.*) s\n', lline) is not None:
                            time = re.sub('(Total time:) (.*) s\n', '\g<2>', lline)
                            sum += float(time)
                            cnt += 1
                
                flag = False

        avg_t = str(sum / cnt)[:8]
        results[type] = avg_t

        log(f'Average {type} time: {avg_t} s')

    log(f'Finish testign Graph: {g_name} with Grammar: {gr_name}...')

    return results


def test_average(tests):
    for test_graph in tests:
        with open(f'results/{test_graph}_average.md', 'w') as fout:
            graphs = glob(f'input/{test_graph}/Graphs/*')
            grammars = glob(f'input/{test_graph}/Grammars/*')

            print(graphs)
            print(grammars)

            fout.write(f'# {test_graph}\n\n')
            
            for gr in sorted(grammars):
                gr_name = filename(gr)
                fout.write(f'## Grammar: {gr_name}\n')
                fout.write('| Graph | Brute | Smart |\n')
                fout.write('|:-----:|:-----:|:-----:|\n')
                for g in sorted(graphs):
                    g_name = filename(g)
                    res = test_one_delete(test_graph, g, gr)
                    res_b = res['brute']
                    res_s = res['smart']
                    fout.write(f'| {g_name} | {res_b} | {res_s} |\n')
                    fout.flush()
                fout.write('\n')


def test_all(tests):
    for test_graph in tests:
        with open(f'results/{test_graph}.md', 'w') as fout:
            graphs = glob(f'input/{test_graph}/Graphs/*')
            grammars = glob(f'input/{test_graph}/Grammars/*')

            fout.write(f'# {test_graph}\n\n')
            
            for gr in sorted(grammars):
                for test_type in TEST_TYPES:
                    gr_name = filename(gr)
                    fout.write(f'## Grammar: {gr_name}\n')
                    fout.write(f'## Test type: {test_type}\n\n')
                    fout.write(f'| Graph | Queries | Matrix Multiplication Amount | Time (s) |\n')
                    fout.write(f'|:-----:|:-------:|:----------------------------:|:--------:|\n')
                    for g in sorted(graphs):
                        g_name = filename(g)
                        queries = glob(f'input/{test_graph}/Queries/{g_name}/{test_type}/*')
                        for type in ['brute', 'smart']:
                            for q in queries:
                                q_name = filename(q)
                                if q_name.startswith(type):
                                    time = None
                                    mul = None
                                    if test_type == 'Construct':
                                        (time, mul) = test_one_graph(test_graph, 'Empty.txt', gr, q)
                                    else:
                                        (time, mul) = test_one_graph(test_graph, g, gr, q)
                                    fout.write(f'| {g_name} | {q_name} | {mul} | {time} |\n')
                                    fout.flush()
                    fout.write('\n')
                        

if __name__ == '__main__':
    test_graphs = list(map(str, sys.argv[1:]))
    init(test_graphs)
    test_all(test_graphs)