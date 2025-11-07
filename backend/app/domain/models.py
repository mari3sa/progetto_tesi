from pydantic import BaseModel, Field
from typing import Literal, List, Union

class NodeLabelConstraint(BaseModel):
    type: Literal["node_label_included"]
    label: str = Field(..., min_length=1)

class EdgeTypeConstraint(BaseModel):
    type: Literal["edge_type_between"]
    from_label: str = Field(..., min_length=1)
    rel_type: str = Field(..., min_length=1)
    to_label: str = Field(..., min_length=1)

Constraint = Union[NodeLabelConstraint, EdgeTypeConstraint]

class ConstraintsPayload(BaseModel):
    constraints: List[Constraint]
