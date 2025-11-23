"""
Modelli Pydantic utilizzati per rappresentare i vincoli applicabili al grafo.

I vincoli sono tipizzati tramite discriminatore `type` e possono descrivere
sia condizioni sui nodi (es. label presenti), sia condizioni sulle relazioni
(es. tipo di arco ammesso tra due label).  
Il payload principale `ConstraintsPayload` raccoglie una lista eterogenea
di vincoli, validati automaticamente da Pydantic.
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Union

# Vincolo che impone che una certa label sia presente nel grafo.
class NodeLabelConstraint(BaseModel):
    type: Literal["node_label_included"]
    label: str = Field(..., min_length=1)

# Vincolo che specifica un tipo di relazione ammessa tra due label.
class EdgeTypeConstraint(BaseModel):
    type: Literal["edge_type_between"]
    from_label: str = Field(..., min_length=1)
    rel_type: str = Field(..., min_length=1)
    to_label: str = Field(..., min_length=1)

# Alias che rappresenta un vincolo generico (uno dei modelli sopra).
Constraint = Union[NodeLabelConstraint, EdgeTypeConstraint]

# Payload principale che contiene la lista dei vincoli.

class ConstraintsPayload(BaseModel):
    constraints: List[Constraint]
