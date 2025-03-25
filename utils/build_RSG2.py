import networkx as nx
import re
import numpy as np
import os
import argparse
from tqdm import tqdm
from itertools import combinations
import multiprocessing as mp

import sys
sys.path.append('.')
from utils.vocab_reader import Vocabulary




class RSG(object):
    
    def __init__(self, raw_train, rel_voc, data_dir):
        self.raw_train = raw_train
        self.rel_voc = rel_voc
        self.data_dir = data_dir
        self.biG, self.triples = self.build_graph()

    def build_graph(self):
        '''
        创建一个有向图，每个三元组 (head, relation, tail) 都会添加两条边，
        分别使用关系 relation 和 'inv_' + relation 作为边的类型。
        '''
        biG = nx.MultiDiGraph()
        total_links = 0
        triple= []
        with open(self.raw_train, 'r') as f_train:
            for line in f_train.readlines():
                total_links = total_links + 1
                tokens = re.split(r'\t|\s', line.strip())
                head = tokens[0]
                relation = tokens[1]
                tail = tokens[2]
                biG.add_edge(head, tail, **{'r_type': relation})
                biG.add_edge(tail, head, **{'r_type': 'inv_' + relation})
                triple.append((head, relation , tail))
                triple.append((tail, 'inv_' + relation , head))
        f_train.close()
        print("number of links in train is:{links}".format(links=total_links))
        return biG,triple
    
    # 获取入度邻域
    def get_in_neighbors(self, head, tail):
        # 头实体入度邻域
        neighbors1 = self.biG.predecessors(head)
        # 尾实体入度邻域
        neighbors2 = self.biG.predecessors(tail)
        return set(list(neighbors1)+list(neighbors2))
    
    # 获取出度邻域
    def get_out_neighbors(self, head, tail):
        # 头实体出度邻域
        neighbors1 = self.biG.successors(head)
        # 尾实体出度邻域
        neighbors2 = self.biG.successors(tail)
        return set(list(neighbors1)+list(neighbors2))

    def get_structure_similarity(self, triple):
        triple1 = triple[0]
        triple2 = triple[1]
        # 获得入度结构相似度
        neighbors1_in = self.get_in_neighbors(triple1[0],triple1[1])
        neighbors2_in = self.get_in_neighbors(triple2[0],triple2[1])
        neighbors1_in.add(triple1[0])
        neighbors1_in.add(triple1[1])
        neighbors2_in.add(triple2[0])
        neighbors2_in.add(triple2[1])
        structure_in_similarity = len(neighbors1_in.intersection(neighbors2_in)) / len(neighbors1_in.union(neighbors2_in))
        
        # 获得出度结构相似度
        neighbors1_out = self.get_out_neighbors(triple1[0],triple1[1])
        neighbors2_out = self.get_out_neighbors(triple2[0],triple2[1])
        neighbors1_out.add(triple1[0])
        neighbors1_out.add(triple1[1])
        neighbors2_out.add(triple2[0])
        neighbors2_out.add(triple2[1])
        structure_out_similarity = len(neighbors1_out.intersection(neighbors2_out)) / len(neighbors1_out.union(neighbors2_out))
        
        structure_similarity = (structure_in_similarity + structure_out_similarity)/2
        
        return structure_similarity

    def get_RSG(self):
        rel_triple=[]
        rel_set ={}        
        for i in tqdm(range(len(self.triples))):
            h1, r1, t1 = self.triples[i]
            for j in range(len(self.triples)):
                h2, r2, t2 = self.triples[j]
                if (h1, t1, r1) != (h2, t2, r2):
                    w = self.get_structure_similarity(self.biG,[h1, t1, r1],[h2, t2, r2])
                    w = int(w*10)
                    if w!=0 and (r1 != 'inv_'+r2 and r2 != 'inv_'+r1) and r1!=r2:
                        if (r1,r2) in rel_set:
                            rel_set[(r1,r2)]+=w
                        else:
                            rel_set[(r1,r2)]=w
        
        for key, value in rel_set.items():
            rel_triple.append([key[0],value,key[1]])
        # 关系词汇路径
        rel_vocabulary= Vocabulary(vocab_file=self.rel_voc)
        # 创建实体和关系的字典
        rel_head_list=[]
        rel_tail_list=[]
        w_list=[]
        # 生成实体和关系的ID表示
        for triple in rel_triple:
            head, relation, tail = triple
            rel_head_list.append(head)
            w_list.append(relation)
            rel_tail_list.append(tail)
        head_list = rel_vocabulary.convert_tokens_to_ids(rel_head_list)
        tail_list = rel_vocabulary.convert_tokens_to_ids(rel_tail_list)
        # 生成关系结构图三元组
        rel_triple2id = []
        for i in range(len(head_list)):
            rel_triple2id.append([head_list[i],w_list[i],tail_list[i]])
        rel_triple2id = np.array(rel_triple2id)
        return rel_triple2id

    def get_RSG2(self):
        rel_triple=[]
        rel_set ={}    
        for (i, (h1, r1, t1)), (j,(h2, r2, t2))in \
            tqdm(combinations(enumerate(self.triples), 2), total=len(self.triples) * (len(self.triples) - 1) // 2):
            if (h1, t1, r1) != (h2, t2, r2):
                w = self.get_structure_similarity([[h1, t1, r1],[h2, t2, r2]])
                w = int(w*10)
                if w!=0 and (r1 != 'inv_'+r2 and r2 != 'inv_'+r1) and r1!=r2:
                    if (r1,r2) in rel_set:
                        rel_set[(r1,r2)]+=w
                    else:
                        rel_set[(r1,r2)]=w
        
        for key, value in rel_set.items():
            rel_triple.append([key[0],value,key[1]])
        # 关系词汇路径
        rel_vocabulary= Vocabulary(vocab_file=self.rel_voc)
        # 创建实体和关系的字典
        rel_head_list=[]
        rel_tail_list=[]
        w_list=[]
        # 生成实体和关系的ID表示
        for triple in rel_triple:
            head, relation, tail = triple
            rel_head_list.append(head)
            w_list.append(relation)
            rel_tail_list.append(tail)
        head_list = rel_vocabulary.convert_tokens_to_ids(rel_head_list)
        tail_list = rel_vocabulary.convert_tokens_to_ids(rel_tail_list)
        # 生成关系结构图三元组
        rel_triple2id = []
        for i in range(len(head_list)):
            rel_triple2id.append([head_list[i],w_list[i],tail_list[i]])
        rel_triple2id = np.array(rel_triple2id)
        return rel_triple2id


    
    def write_RSG(self):
        rel_triple2id = self.get_RSG2()
        with open(self.data_dir, "w") as file:
            for rel_triple in rel_triple2id:
                file.write('\t'.join(map(str, rel_triple)) + '\n')
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task",
        type=str,
        #required=True,
        default='WN18RR_v1',
        choices=[
            'fb237_v1', 'fb237_v2', 'fb237_v3', 'fb237_v4', 
            'WN18RR_v1', 'WN18RR_v2', 'WN18RR_v3', 'WN18RR_v4',
            'fb237_v1_ind', 'fb237_v2_ind', 'fb237_v3_ind', 'fb237_v4_ind',
            'WN18RR_v1_ind', 'WN18RR_v2_ind', 'WN18RR_v3_ind', 'WN18RR_v4_ind'
        ])
    args = parser.parse_args()
    data_dir = os.path.join(os.getcwd(), 'data_preprocessed', args.task, 'RSG2.txt') # 处理后RSG保存地址
    raw_train = os.path.join(os.getcwd(), 'dataset', args.task, 'train.txt')
    vocab_path = os.path.join('data_preprocessed', args.task, 'vocab_rel.txt')
    rsg = RSG(raw_train, vocab_path, data_dir)
    print('Build Relational Structure Graph...')
    rel_triple = rsg.write_RSG()
    print('finish building RSG')
    