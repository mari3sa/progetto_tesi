# progetto_tesi
Questo repository contiene un esempio di grafo costruito in Neo4j e utilizzato per il calcolo delle misure di inconsistenza applicate a relazioni familiari.

Il grafo è composto da sette persone:

Alice, Bryan, Clara, David, Ester, Frank, Grace.

Le relazioni includono varie tipologie parentali:
child_of, son_of, grandson_of, granddaughter_of, brother_of, sister_of, cousin_of, nephew_of.

Query Cypher per creare il grafo su Neo4j:

CREATE (Alice:Person {name: "Alice"}) 
CREATE (Bryan:Person {name: "Bryan"})
CREATE (Clara:Person {name: "Clara"})
CREATE (David:Person {name: "David"}) 
CREATE (Ester:Person {name: "Ester"})
CREATE (Frank:Person {name: "Frank"})
CREATE (Grace:Person {name: "Grace"}) 

CREATE (Bryan)-[:son_of]->(Alice) 
CREATE (Bryan)-[:child_of]->(Alice) 

CREATE (Bryan)-[:brother_of]->(Clara) 
CREATE (Clara)-[:sister_of]->(Bryan) 
CREATE (Clara)-[:child_of]->(Alice) 

CREATE (David)-[:son_of]->(Bryan)
CREATE (David)-[:grandson_of]->(Alice)  
CREATE (David)-[:child_of]->(Bryan) 
CREATE (David)-[:brother_of]->(Ester) 

CREATE (Ester)-[:sister_of]->(Frank) 
CREATE (Ester)-[:sister_of]->(David) 
CREATE (Ester)-[:cousin_of]->(Grace) 
CREATE (Ester)-[:child_of]->(Bryan) 

CREATE (Frank)-[:child_of]->(Bryan)
CREATE (Frank)-[:cousin_of]->(Grace)
CREATE (Frank)-[:nephew_of]->(Clara) 

CREATE (Grace)-[:child_of]->(Clara) 
CREATE (Grace)-[:granddaughter_of]->(Alice)

MATCH (n)-[r]->(m) RETURN n,r,m;
