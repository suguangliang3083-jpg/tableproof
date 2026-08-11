"""TableProof public package interface."""

__version__ = "0.1.1"

from .audit import audit_join, audit_many
from .models import JoinSpec, TableProofError

__all__ = ["JoinSpec", "TableProofError", "audit_join", "audit_many"]
