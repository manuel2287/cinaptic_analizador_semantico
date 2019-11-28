import json
import itertools
import wikipedia
import pickle
from cinaptic.cinaptic.api.library.semantic.repository.Neo4J import config
from neomodel import db
from cinaptic.cinaptic.api.library.semantic.clients.textrazorClient import TextRazorClient
from operator import itemgetter
from pypher import Pypher, __


WEIGHTS = [1.0, 0.5, 0.3333333333333333, 0.25, 0.2, 0.16666666666666666, 0.14285714285714285, 0.125, 0.1111111111111111, 0.1, 0.09090909090909091, 0.08333333333333333, 0.07692307692307693, 0.07142857142857142, 0.06666666666666667, 0.0625, 0.058823529411764705, 0.05555555555555555, 0.05263157894736842, 0.05, 0.047619047619047616, 0.045454545454545456, 0.043478260869565216, 0.041666666666666664, 0.04, 0.038461538461538464, 0.037037037037037035, 0.03571428571428571, 0.034482758620689655, 0.03333333333333333, 0.03225806451612903, 0.03125, 0.030303030303030304, 0.029411764705882353, 0.02857142857142857, 0.027777777777777776, 0.02702702702702703, 0.02631578947368421, 0.02564102564102564, 0.025, 0.024390243902439025, 0.023809523809523808, 0.023255813953488372, 0.022727272727272728, 0.022222222222222223, 0.021739130434782608, 0.02127659574468085, 0.020833333333333332, 0.02040816326530612, 0.02, 0.0196078431372549, 0.019230769230769232, 0.018867924528301886,
           0.018518518518518517, 0.01818181818181818, 0.017857142857142856, 0.017543859649122806, 0.017241379310344827, 0.01694915254237288, 0.016666666666666666, 0.01639344262295082, 0.016129032258064516, 0.015873015873015872, 0.015625, 0.015384615384615385, 0.015151515151515152, 0.014925373134328358, 0.014705882352941176, 0.014492753623188406, 0.014285714285714285, 0.014084507042253521, 0.013888888888888888, 0.0136986301369863, 0.013513513513513514, 0.013333333333333334, 0.013157894736842105, 0.012987012987012988, 0.01282051282051282, 0.012658227848101266, 0.0125, 0.012345679012345678, 0.012195121951219513, 0.012048192771084338, 0.011904761904761904, 0.011764705882352941, 0.011627906976744186, 0.011494252873563218, 0.011363636363636364, 0.011235955056179775, 0.011111111111111112, 0.01098901098901099, 0.010869565217391304, 0.010752688172043012, 0.010638297872340425, 0.010526315789473684, 0.010416666666666666, 0.010309278350515464, 0.01020408163265306, 0.010101010101010102, 0.01]
DBPEDIA_SPARKQL_ENDPOINT = "http://dbpedia.org/sparql"
WIKIPEDIA_URLBASE = "http://en.wikipedia.org/wiki/"
textrazorclient = TextRazorClient()
p = Pypher()

class GraphGen:
    def __init__(self):
        self.entitiesSeen = set()
        self.tuplesSeen = set()
        self.computed = set()
        self.remnants = set()
        # self.top = 100
        self.top = 50
        self.topMatching = None
        # self.topMatching = 3
        self.levelLimit = 2
        self.nameGraph = 'test'

    def getListEntitiesFromWiki(self, entity=None, top=None):
        withoutRelevanceZero = []
        if entity is not None:
            entitiesFromWiki = self.getTextRazorResponse(entity)
            entidadesWiki = list(
                filter(lambda y: y['id'] != entity, map(lambda x: self.parseTupleToDict(x), entitiesFromWiki)))
            sortedListEntities = sorted(entidadesWiki, key=itemgetter(
                'relevance', 'confidence'), reverse=True)
            # only for duplicate filter purposes
            self.entitiesSeen = set()
            # only for duplicate filter purposes
            withoutDuplicates = list(
                filter(lambda x: self.avoidDuplicate(x), sortedListEntities))
            withoutRelevanceZero = list(
                filter(lambda x: x["relevance"] > 0, withoutDuplicates))
        return withoutRelevanceZero[:top] if top is not None else withoutRelevanceZero

    def avoidDuplicate(self, entity):
        if entity['id'] in self.entitiesSeen:
            return False
        self.entitiesSeen.add(entity['id'])
        return True

    def parseDbpediaResponse(self, result=None):
        if (result is not None):
            return result['wikiurl']['value']
        return ''

    def buildQuery(self, entity):
        return f"""
        SELECT ?wikiurl
        WHERE {{
            dbr:{entity} foaf:isPrimaryTopicOf ?wikiurl
        }}
        """

    def getTextRazorResponse(self, entity=None):
        textRazorResponse = {}
        if entity is not None:
            # textRazorResponse = set(map(lambda x: self.parseTextRazorResponse(x), set(textrazorclient.get_entities_from_url(url).entities())))
            textRazorResponse = set(map(lambda x: self.parseTextRazorResponse(x), set(
                textrazorclient.get_entities_from_text(self.getContentFromWiki(entity)).entities())))
        return textRazorResponse

    def getTextRazorResponseFromSK(self, sk=None):
        textRazorResponse = {}
        if sk is not None:
            textRazorResponse = set(map(lambda x: self.parseTextRazorResponse(x), set(
                textrazorclient.get_entities_from_text(sk).entities())))
        return textRazorResponse

    def parseTextRazorResponse(self, textRazorResponse=None):
        responseDict = ()
        if textRazorResponse is not None:
            responseDict = (
                textRazorResponse.id,
                textRazorResponse.confidence_score,
                textRazorResponse.relevance_score,
                textRazorResponse.wikipedia_link,
            )
        return responseDict

    def parseTupleToDict(self, tupla=None):
        """
        Return a dict from the entity tuple.
        """
        responseDict = {}
        if tupla is not None:
            responseDict = {
                "id": tupla[0],
                "confidence": tupla[1],
                "relevance": tupla[2],
                "wikiurl": tupla[3]
            }
        return responseDict

    def getDirectMatchingList(self, entity1, entity2, listEntity1=[], listEntity2=[], top=None):
        idList1 = [x['id'] for x in listEntity1]
        idList2 = [x['id'] for x in listEntity2]
        listMatched = list(filter(lambda y: y is not None, map(lambda x: self.matching(
            x, x['id'] in idList1, listEntity1, listEntity2), listEntity2)))
        if entity1 in idList2:
            entity = {"id": entity1}
            listMatched.append(self.matching(entity,
                                             True, listEntity1, listEntity2))
        if entity2 in idList1:
            entity = {"id": entity2}
            listMatched.append(self.matching(entity,
                                             True, listEntity1, listEntity2))
        sortedListMatched = sorted(
            listMatched, key=itemgetter('relevance'), reverse=True)
        return sortedListMatched[:top] if top is not None else sortedListMatched

    def calculateWeight(self, value1=0, value2=0, index1=0, index2=0):
        return (value1 * WEIGHTS[index1]) + (value2 * WEIGHTS[index2])

    def matching(self, entity=None, isMatch=False, listEntity1=[], listEntity2=[]):
        if entity is not None and isMatch:
            item1 = next(
                (item for item in listEntity1 if item['id'] == entity['id']), None)
            item2 = next(
                (item for item in listEntity2 if item['id'] == entity['id']), None)
            return {
                "id": entity['id'],
                "relevance": self.calculateWeight(0 if item1 is None else item1['relevance'], 0 if item2 is None else item2['relevance'], 0 if item1 is None else listEntity1.index(item1), 0 if item2 is None else listEntity2.index(item2))
            }
        return None

    def getContentFromWiki(self, entity=None):
        if entity is not None:
            try:
                wp = wikipedia.page(title=entity)
                return wp.content
            except Exception as e:
                print(e)
                pass
        return ''

    def computeTuple(self, tupla=(None, None), currentLevel=None, topTR=None, topMatching=None):
        """
        Compute a tuple (e1, e2) and return the matching list of tuples in lexicographic order
        """
        if currentLevel is None:
            return []
        if topTR is None:
            topTR = self.top
        if topMatching is None:
            topMatching = self.topMatching
        result = []
        if tupla[0] is not None and tupla[1] is not None:
            if tupla in self.computed:
                return []
            else:
                self.computed.add(tupla)
            listEntity1 = self.getListEntitiesFromWiki(tupla[0], topTR)
            listEntity2 = self.getListEntitiesFromWiki(tupla[1], topTR)
            result = self.getDirectMatchingList(tupla[0], tupla[1],
                                                listEntity1, listEntity2, topMatching)
            # aca se persistirian los datos en neo4j
            [self.persistTriple(tupla, entity) for entity in result]
            print('+++++++++++++++++++++++++++++++++++++++++++++++')
            [print(f"{tupla[0]} --> {entity['id']} <-- {tupla[1]}") for entity in result]

            if currentLevel + 1 <= self.levelLimit:
                auxList = [{"id": e}
                           for e in tupla if e not in [r['id'] for r in result]]
                result = auxList + result
        return self.getLexicographicOrderedTuplesList(result)

    def getLexicographicOrderedTuplesList(self, matchingList=[]):
        """
        Return tuples in lexicographic order from the matching list
        """
        try:
            mlistIds = [entity['id'] for entity in matchingList]
            mlistIdsOrdered = sorted(mlistIds)
            result = [(x, y)
                      for x in mlistIdsOrdered for y in mlistIdsOrdered if x < y]
        except Exception as e:
            print(e)
            result = []
            pass
        return result

    def computeLevel(self, tuplesList=[], level=None):
        """
        Compute a level: [(e1, e2)...], level => [(ei, ej)...], level + 1
        """
        if level is None or level > self.levelLimit:
            return [], level+1
        if len(tuplesList) > 0:
            print(f"""nivel {level}:""")
            newTuplesList = [self.computeTuple(
                tupla, level) for tupla in tuplesList]
            newTuplesList = list(itertools.chain.from_iterable(newTuplesList))
        return self.computeLevel(newTuplesList, level+1)

    def executeEntityTuple(self, entityTuple=(None, None)):
        """
        Execute the script for a tuple of entities and persist data in a Neo4J graph
        """
        if entityTuple[0] is not None and entityTuple[1] is not None:
            try:
                self.nameGraph = f"""{entityTuple[0]}-{entityTuple[1]}"""
                if not self.isGraphCreated():
                    tuplesList = [self.getLexicographicTuple(
                        entityTuple[0], entityTuple[1])]
                    self.computeLevel(tuplesList, 1)
                    self.persistEntitiesWeights()
                    results, headers = self.getOrderedEntitiesByWeight()
                    data = { 'results': results }
                    print(data)
                    self.saveResults(data)
                    return results, headers
            except Exception as e:                
                print(e)        
        return [], ()

    def getLexicographicTuple(self, entity1=None, entity2=None):
        tupla = None
        if entity1 is not None and entity2 is not None:
            if entity1 < entity2:
                tupla = tuple([entity1, entity2])
            else:
                tupla = tuple([entity2, entity1])
        return tupla

    def persistTriple(self, tupla = (None, None), relationEntity = None, nameGraph = None):
        if nameGraph is None:
            nameGraph = self.nameGraph
        if tupla[0] is not None and tupla[1] is not None and relationEntity is not None:
            try:
                p.reset()
                if tupla[0] != relationEntity and tupla[1] != relationEntity:
                    p.MERGE.node('a', 'Entidad', name=tupla[0], idGraph=nameGraph)
                    self.executeQuery()
                    p.MERGE.node('b', 'Entidad', name=tupla[1], idGraph=nameGraph)
                    self.executeQuery()
                    p.MERGE.node('c', 'Entidad', name=relationEntity['id'], idGraph=nameGraph)
                    self.executeQuery()
                    if tupla[0] != relationEntity['id']:
                        p.MATCH.node('e1', 'Entidad', name=tupla[0], idGraph=nameGraph).MATCH.node('er', 'Entidad', name=relationEntity['id'], idGraph=nameGraph).CREATE.node('e1').rel_out(labels='RELATION', relevance=relationEntity['relevance'], idGraph=nameGraph).node('er')
                        self.executeQuery()
                    if tupla[1] != relationEntity['id']:
                        p.MATCH.node('e2', 'Entidad', name=tupla[1], idGraph=nameGraph).MATCH.node('er', 'Entidad', name=relationEntity['id'], idGraph=nameGraph).CREATE.node('e2').rel_out(labels='RELATION', relevance=relationEntity['relevance'], idGraph=nameGraph).node('er')
                        self.executeQuery()
            except Exception as e:
                print(e)
                pass

    def persistEntitiesWeights(self, nameGraph = None):
        if nameGraph is None:
            nameGraph = self.nameGraph
        try:
            p.reset()
            p.MATCH.node('e1', 'Entidad', idGraph=nameGraph).rel_in('r').node(idGraph=nameGraph)
            p.WITH('e1', __.SUM(__.r.Property('relevance')).alias('weight'))
            p.SET(__.e1.__weight__ == __.weight)
            self.executeQuery()
        except Exception as e:
            print(e)
            pass
        
    def executeQuery(self):
        results, header = db.cypher_query(str(p), params=p.bound_params)
        p.reset()
        return results, header

    def getOrderedEntitiesByWeight(self, nameGraph = None):
        results = []
        headers = ()
        if nameGraph is None:
            nameGraph = self.nameGraph
        try:
            p.reset()
            p.MATCH.node('e1','Entidad', idGraph=nameGraph).RETURN(__.e1.Property('name').alias('Entidad'), __.e1.Property('weight').alias('Weight')).ORDERBY(__.e1.Property('weight')).DESC()
            results, headers = self.executeQuery()
        except Exception as e:
            print(e)
            pass
        return results, headers

    def saveResults(self, results = None, nameGraph = None):
        path = None
        if nameGraph is None:
            nameGraph = self.nameGraph
        if results is not None and nameGraph is not None:
            path = f'graphs/{nameGraph}.pickle'
            with open(path, 'wb') as f:
                pickle.dump(results, f, pickle.HIGHEST_PROTOCOL)
        return path

    def isGraphCreated(self, nameGraph = None):
        if nameGraph is None:
            nameGraph = self.nameGraph
        if nameGraph is not None:
            p.reset()
            p.MATCH().node('e1',idGraph=nameGraph).RETURN('e1')
            results, headers = self.executeQuery()
            return len(results) > 0
        return False

        
        

enex = GraphGen()

entity1 = 'Risotto'
entity2 = 'Paella'

# 
# top = 100
# listEntity1 = enex.getListEntitiesFromWiki(entity1, top)
# listEntity2 = enex.getListEntitiesFromWiki(entity2, top)
# result = enex.getDirectMatchingList(entity1, entity2, listEntity1, listEntity2)
# print(len(result))
# eljson = {
#     entity1: listEntity1,
#     entity2: listEntity2,
#     'results': result,
#     }
# with open(f'test.json', 'w') as file:
#     file.write(json.dumps(eljson))
# 

enex.executeEntityTuple((entity1, entity2))

# enex.persistEntitiesWeights('Risotto-Paella')