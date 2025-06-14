from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Awaitable, Optional, Union

from beartype import beartype

# Forward declaration for type checking without circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import Response, Request


class ExecuteAction(Enum):
    """Actions available for Handler execution."""

    RETURN = auto()
    MODIFY = auto()
    ALL = auto()


@beartype
@dataclass(frozen=True)
class Execute:
    """Configuration for Handler behaviour."""

    action: ExecuteAction
    response_modify: Optional[Callable[["Response"], Union["Response", Awaitable["Response"]]]] = None
    request_modify: Optional[Callable[["Request"], Union["Request", Awaitable["Request"]]]] = None
    max_responses: Optional[int] = None
    max_modifications: Optional[int] = None

    def __post_init__(self) -> None:
        if self.action == ExecuteAction.RETURN:
            # For RETURN only max_responses is relevant
            if self.response_modify is not None:
                raise ValueError("RETURN action should not have response_modify")
            if self.request_modify is not None:
                raise ValueError("RETURN action should not have request_modify")
        elif self.action == ExecuteAction.MODIFY:
            if self.response_modify is None and self.request_modify is None:
                raise ValueError("MODIFY action requires at least one of response_modify or request_modify")
            if self.max_modifications is None:
                raise ValueError("MODIFY action requires max_modifications")
        elif self.action == ExecuteAction.ALL:
            if self.response_modify is None and self.request_modify is None:
                raise ValueError("ALL action requires at least one of response_modify or request_modify")
            if self.max_modifications is None:
                raise ValueError("ALL action requires max_modifications")
            if self.max_responses is None:
                raise ValueError("ALL action requires max_responses")

    # Convenient constructors
    @classmethod
    def RETURN(cls, max_responses: Optional[int] = 1) -> "Execute":
        return cls(action=ExecuteAction.RETURN, max_responses=max_responses)

    @classmethod
    def MODIFY(
        cls,
        response_modify: Optional[Callable[["Response"], Union["Response", Awaitable["Response"]]]] = None,
        request_modify: Optional[Callable[["Request"], Union["Request", Awaitable["Request"]]]] = None,
        max_modifications: Optional[int] = 1,
    ) -> "Execute":
        if response_modify is None and request_modify is None:
            raise ValueError("MODIFY action requires at least one of response_modify or request_modify")
        
        return cls(
            action=ExecuteAction.MODIFY,
            response_modify=response_modify,
            request_modify=request_modify,
            max_modifications=max_modifications,
        )

    @classmethod
    def ALL(
        cls,
        response_modify: Optional[Callable[["Response"], Union["Response", Awaitable["Response"]]]] = None,
        request_modify: Optional[Callable[["Request"], Union["Request", Awaitable["Request"]]]] = None,
        max_responses: Optional[int] = 1,
        max_modifications: Optional[int] = 1,
    ) -> "Execute":
        if response_modify is None and request_modify is None:
            raise ValueError("ALL action requires at least one of response_modify or request_modify")
        
        return cls(
            action=ExecuteAction.ALL,
            response_modify=response_modify,
            request_modify=request_modify,
            max_responses=max_responses,
            max_modifications=max_modifications,
        )
