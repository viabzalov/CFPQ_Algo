from glob import glob
import subprocess as sp
import logging
import random
import sys
import os
import re

logging.basicConfig(format=u'[%(asctime)s]:%(filename)s:%(funcName)s:%(lineno)d:%(message)s', level=logging.INFO)

TEST_GRAPHS = [
    'FullGraph',
    'WorstCase',
    'SparseGraph',
    'ScaleFree',
    'RDF',
]

TEST_TYPES = [
    'Construct',
    'Correctness',
]


CFPQ_DATA = 'deps/CFPQ_Data/'


def filename(path):
    return os.path.splitext(os.path.basename(path))[0]


def filesize(path):
    r = sp.run(f'wc -l {path}', capture_output=True, shell=True)
    return int(r.stdout.split()[0].decode('utf-8'))


def init(tests, test_types):
    logging.info('Start building executables')
    sp.run('make', shell=True)
    logging.info('Finish building executables')

    if os.path.exists('input') is False:
        logging.info('Created input directory')
        os.mkdir('input')

    if os.path.exists('results') is False:
        logging.info('Created results directory')
        os.mkdir('results')

    if os.path.exists('Empty.txt') is False:
        sp.run('touch Empty.txt', shell=True)

    for test in tests:
        if os.path.exists(f'input/{test}') is False:
            os.mkdir(f'input/{test}')
            logging.info(f'Created input/{test} directory')

            os.mkdir(f'input/{test}/Graphs')
            logging.info(f'Created input/{test}/Graphs directory')

            os.mkdir(f'input/{test}/Grammars')
            logging.info(f'Created input/{test}/Grammars directory')

            os.mkdir(f'input/{test}/Queries')
            logging.info(f'Created input/{test}/Queries directory')

    pwd = os.path.abspath('.')

    if os.path.exists(f'{CFPQ_DATA}data/FullGraph/Matrices') is False:
        logging.info('Start initialize CFPQ_Data')
        cur_dir = f'{pwd}/deps/CFPQ_Data'
        cfpq_data_url = 'https://github.com/viabzalov/CFPQ_Data.git deps/CFPQ_Data'
        sp.run(f'git clone {cfpq_data_url}', shell=True)
        sp.run(f'pip3 install -r requirements.txt', cwd=cur_dir, shell=True)
        sp.run(f'python3 init.py', cwd=cur_dir, shell=True)
        logging.info('Finish initialize CFPQ_Data')

    for test in tests:
        logging.info(f'Start initialize {test}')
        graphs = glob(f'{CFPQ_DATA}data/{test}/Matrices/*')
        for g in sorted(graphs, key=filesize):
            g_txt = f'{filename(g)}.txt'
            if filesize(g) > int(1e5):
                continue
            logging.info(f'Start initialize {test} Graph:{g_txt}')
            if os.path.exists(f'input/{test}/Graphs/{g_txt}') is False:
                sp.run(f'python3 {CFPQ_DATA}tools/RDF_to_triple/converter.py {g} {CFPQ_DATA}data/{test}/convconfig', shell=True)
                sp.run(f'mv {CFPQ_DATA}data/{test}/Matrices/{g_txt} input/{test}/Graphs/{g_txt}', shell=True)
            if 'Construct' in test_types:
                construct_graph_queries(test, g_txt)
            if 'Correctness' in test_types:
                correctness_graph_queries(test, g_txt)
            logging.info(f'Finish initialize {test} Graph:{g_txt}')

        grammars = glob(f'{CFPQ_DATA}data/{test}/Grammars/*')
        for gr in sorted(grammars, key=filesize):
            gr_cnf = f'{filename(gr)}_cnf.txt'
            logging.info(f'Start initialize {test} Grammar:{gr_cnf}')
            if os.path.exists(f'input/{test}/Grammars/{gr_cnf}') is False:
                sp.run(f'python3 {CFPQ_DATA}tools/grammar_to_cnf/grammar_to_cnf.py {gr} -o input/{test}/Grammars/{gr_cnf}', shell=True)
            logging.info(f'Finish initialize {test} Grammar:{gr_cnf}')
        logging.info(f'Finish initialize {test}')


def construct_graph_queries(test, graph):
    q_dir = f'input/{test}/Queries/{filename(graph)}/Construct/'
    if os.path.exists(q_dir) is False:
        os.makedirs(q_dir, exist_ok=True)
    for type in ['brute', 'smart']:
        with open(f'input/{test}/Graphs/{graph}', 'r') as fin:
            q_path = q_dir + f'{type}.txt'
            with open(q_path, 'w') as fout:
                logging.info(f'Start adding queries to {q_path}')
                for line in fin:
                    v, edge, to = line.split()
                    fout.write(f'{type}-edge-add {v} {to} {edge}\n')
                logging.info(f'Finish adding queries to {q_path}')


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
                logging.info(f'Start adding queries to {q_path}')
                for line in fin:
                    v, edge, to = line.split()
                    fout.write(f'{type}-edge-add {v} {to} {edge}\n')
                for i in range(min_v, max_v + 1):
                    for j in range(min_v, max_v + 1):
                        if i != j:
                            fout.write(f'find-path {i} {j}\n')
                logging.info(f'Finish adding queries to {q_path}')


def test_one_graph(test, graph, grammar, queries, save_log, graph_name):
    g_name = filename(graph)
    gr_name = filename(grammar)
    q_name = filename(queries)

    if os.path.exists(test) is False:
        os.makedirs(test, exist_ok=True)

    results_path = f'{test}/{test}_{g_name}_{gr_name}_{q_name}_log.txt'

    logging.info(f'Start testing {test} with Graph: {graph_name} with Grammar: {gr_name} and Queries: {q_name}')

    time = 0
    cnt = 0

    n = 100
    q_size = filesize(queries)
    if q_size > int(4e4):
        n = 2
    elif q_size > int(1e4):
        n = 10

    for i in range(n):
        sp.run(f'./main {graph} {grammar} {queries} > {results_path}', shell=True)
        res = get_time(results_path)
        logging.info(f'Total time for {i}th run: {res} s')
        if res is not None:
            time += res
            cnt += 1

    logging.info(f'Average time: {time / cnt} s')

    if save_log is False:
        os.remove(results_path)

    logging.info(f'Finish testing {test} with Graph: {graph_name} with Grammar: {gr_name} and Queries: {q_name}')

    return round(time / cnt, 6)


def get_time(results_path):
    time = None
    with open(results_path, 'r') as fin:
        for line in fin:
            if re.fullmatch('(Total time:) (.*) s\n', line) is not None:
                time = re.sub('(Total time:) (.*) s\n', '\g<2>', line)
    if time is None:
        return None
    else:
        return round(float(time), 6)


def test_all(tests, test_types):
    for test_graph in tests:
        with open(f'results/{test_graph}.md', 'w') as fout:
            graphs = glob(f'input/{test_graph}/Graphs/*')
            grammars = glob(f'input/{test_graph}/Grammars/*')

            fout.write(f'# {test_graph}\n\n')

            for gr in sorted(grammars, key=filesize):
                if 'Construct' in test_types:
                    gr_name = filename(gr)
                    fout.write(f'## Grammar: {gr_name}\n')
                    fout.write(f'## Test type: Construct\n\n')
                    fout.write(f'| Graph | Brute | Smart |\n')
                    fout.write(f'|:-----:|:-----:|:-----:|\n')
                    for g in sorted(graphs, key=filesize):
                        g_name = filename(g)
                        results = {}
                        for type in ['brute', 'smart']:
                            qrs = f'input/{test_graph}/Queries/{g_name}/Construct/{type}.txt'
                            time = None
                            time = test_one_graph(test_graph, 'Empty.txt', gr, qrs, False, g_name)
                            results[type] = time
                        result_brute = results['brute']
                        result_smart = results['smart']
                        fout.write(f'| {g_name} | {result_brute} | {result_smart} |\n')
                        fout.flush()
                    fout.write('\n')

                if 'Correctness' in test_types:
                    gr_name = filename(gr)
                    fout.write(f'## Grammar: {gr_name}\n')
                    fout.write(f'## Test type: Correctness\n\n')
                    fout.write(f'| Graph | equal(Brute, Smart) |\n')
                    fout.write(f'|:-----:|:-------------------:|\n')
                    for g in sorted(graphs, key=filesize):
                        g_name = filename(g)
                        for type in ['brute', 'smart']:
                            qrs = f'input/{test_graph}/Queries/{g_name}/Correctness/{type}.txt'
                            test_one_graph(test_graph, 'Empty.txt', gr, qrs, True, g_name)
                        brute_log = f'{test_graph}/{test_graph}_Empty_{gr_name}_brute_log.txt'
                        smart_log = f'{test_graph}/{test_graph}_Empty_{gr_name}_smart_log.txt'
                        sp.run(f'diff {brute_log} {smart_log} | grep path > diff_log', shell=True)
                        res = (os.stat('diff_log').st_size == 0)
                        fout.write(f'| {g_name} | {res} |\n')
                        fout.flush()
                    fout.write('\n')


if __name__ == '__main__':
    test_graphs = list(map(str, sys.argv[1:]))
    init(test_graphs, ['Construct'])
    test_all(test_graphs, ['Construct'])