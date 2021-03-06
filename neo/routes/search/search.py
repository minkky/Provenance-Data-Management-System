# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 14:50:29 2019

@author: SookmyungWomensUniv
"""
import sys, time

from itertools import product

from neo4j import GraphDatabase

def check_nodeLabel(tx, keyword):
	checkPerson = (tx.run("MERGE (referee:Person{name: $keyword} )"
					   "RETURN count(referee)>=1 "
					   "as check ", keyword = keyword)).value()[0]
	checkData = (tx.run("MERGE (referee:Data{name: $keyword} )"
						"RETURN count(referee)>=1 "
					   "as check ", keyword = keyword)).value()[0]
	checkActivity = (tx.run("MERGE (referee:Activity{name: $keyword} )"
					   "RETURN count(referee)>=1 "
					   "as check ", keyword = keyword)).value()[0]
	if(checkPerson):
		nodeLabel = "Person"
	elif(checkData):
		nodeLabel = "Data"
	elif(checkActivity):
		nodeLabel = "Activity"
	return nodeLabel

# next (iter (k1nodes[0].labels)) : frozenset 값 얻는법
def get_nodes(tx, keyword, nodeLabel):
	nodes = (tx.run("MERGE (referee: " + nodeLabel + " {name:$keyword}) "
					"RETURN referee"
					, nodeLabel = nodeLabel, keyword = keyword)).values()
	return nodes


def shortestPath(tx, n1, n2):

	length = (tx.run("MATCH (k1:"+next(iter(n1[0].labels))+"{ name: $k1_name, affiliation: $k1_aff }),(k2: " + next(iter(n2[0].labels))+ " { name: $k2_name, affiliation : $k2_aff }), "
					"p = shortestPath((k1)-[*]-(k2)) "
					"RETURN p, length(p)" 
					, k1_name = n1[0]["name"], k1_aff = n1[0]["affiliation"]
					, k2_name = n2[0]["name"], k2_aff = n2[0]["affiliation"])).values()

	if length:
		return length

# proposed
if __name__ == "__main__":
	driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "wowhi223"))

	with driver.session() as session:
		keywords = []
		for i in range(len(sys.argv)-1):
			keywords.append(sys.argv[i+1])

		#keywords = ['성현제', '안정원'] #, '김칫국']
		kLabels = []
		kNodes = []

		start_time = time.time()
		
		for i in range(len(keywords)):
			kLabels.append(session.read_transaction(check_nodeLabel,  keyword= keywords[i]))

		for i in range(len(keywords)):
			kNodes.append(session.read_transaction(get_nodes, keyword= keywords[i], nodeLabel = kLabels[i]))    

		candidN = list(product(*kNodes))

		#initialize subgraph g and N

		g = []
		N = []
		graphs = [] # pair 저장

		for k in range(len(candidN)):

			N = list(candidN[k])
			nodeSum = len(candidN[k])

			path = []
			pathLen = []
			#print("k : ", k)
			flag = True
			for i in range(len(N)):

				pathTmp = []
				pathLenTmp = []
				#print("i 한다 : " , i)
				if not flag:
					break
				for j in range(i+1, len(N)):
					#print(i, N[i])
					#print(j, N[j])
					shortP = session.read_transaction(shortestPath, n1 = N[i], n2 = N[j])
					
					if shortP is not None:
						#print(shortP[0])
						pathTmp.append(shortP[0][0])
						pathLenTmp.append(shortP[0][1])
					else:
						#print(N[i], N[j] , "경로 없음")
						flag = False  
						break
				path.append(pathTmp)
				pathLen.append(pathLenTmp)  
			'''
				print("j 반복 끝")
			print("i 반복 끝")
			print("pathLen: ", pathLen)
			print("path: " , path)
			print(" ")
			'''
			#algorithm
			if pathLen and flag:
				#print("N : ", N)
				g.append(N[0])
				del N[0]
				graphs.append([])

				for i in range(nodeSum-1):
					'''
					print("  i : ", i)
					print("pathLen: ", pathLen)
					print("path: " , path)
					'''
					shortestLenIndex = pathLen[i].index(min(pathLen[i]))

					graphs[k].append(path[i][shortestLenIndex])
					g.append(N[shortestLenIndex])
					del N[shortestLenIndex]
					#print("g: ",g)
		
				#print("="*100)
				#'''
				
				N = []
				g = []
			else:

				graphs.append([])


		results = []
		for each in graphs:
			if each:
				results.append(each) 
		
		resultLen = []
		for each in results:
			sumLen = 0
			for i in range(len(keywords)-1):
				sumLen = sumLen + len(each[i])
			resultLen.append(sumLen)
		resultIndex = sorted(range(len(resultLen)), key=lambda k: resultLen[k])         
		ranking = []
		for i in resultIndex[:3]:
			ranking.append(results[i])

		resultOut = ''
		startNodeLabel = []
		endNodeLabel =[]
		
		startNodeProper = []
		endNodeProper = []
		
		matchCypher = 'MATCH '
		withCypher = ' WITH personA, personB'
		spCypher = ' MATCH p = shortestPath((personA)-[*]-(personB))'
		returnCypher = ' RETURN p' 
		if len(keywords) == 3:
			withCypher = withCypher + " ,personC, personD"
			spCypher = spCypher + " MATCH p2 = shortestPath((personC)-[*]-(personD))"
			returnCypher = returnCypher + ", p2"       

		for i in range(len(ranking)):
			pA = " (personA:" + str(next(iter(ranking[i][0].start_node.labels))) + "{name: " + "'"+ str(ranking[i][0].start_node['name']) +"'"+ ", affiliation: " + "'"+ str(ranking[i][0].start_node['affiliation']) + "'"+ "})"
			pB = " , (personB:" + str(next(iter(ranking[i][0].end_node.labels))) + "{name: " + "'"+ str(ranking[i][0].end_node['name']) +"'"+ ", affiliation: " +"'"+ str(ranking[i][0].end_node['affiliation']) +"'"+ "})"        
			if len(keywords) == 3:    
				pC = " , (personC:" + str(next(iter(ranking[i][1].start_node.labels))) + "{name: " + "'"+ str(ranking[i][1].start_node['name']) +"'"+ ", affiliation: " + "'"+ str(ranking[i][1].start_node['affiliation']) + "'"+ "})"
				pD = " , (personD:" + str(next(iter(ranking[i][1].end_node.labels))) + "{name: " + "'"+ str(ranking[i][1].end_node['name']) +"'"+ ", affiliation: " +"'"+ str(ranking[i][1].end_node['affiliation']) +"'"+ "})"
			if len(keywords) == 2:
				outTemp = matchCypher + pA + pB + withCypher + spCypher + returnCypher
			elif len(keywords) == 3:    
				outTemp = matchCypher + pA + pB + pC + pD + withCypher + spCypher + returnCypher

			resultOut = resultOut + "/" + outTemp 
        
        
	driver.close()
	#print("/MATCH (personA:Person { name: '양유정', affiliation: '한국인터넷진흥원'}), (personB:Person { name: '서민지', affiliation: '한국보건산업진흥원' }) WITH personA, personB MATCH p = shortestPath((personA)-[*]-(personB)) RETURN p/")
	print(resultOut + "/")