from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Awaitable, Optional, Union

from beartype import beartype

# Forward declaration for type checking without circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import Response


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
    callback: Optional[Callable[["Response"], Union["Response", Awaitable["Response"]]]] = None
    max_responses: Optional[int] = None
    max_modifications: Optional[int] = None

    def __post_init__(self) -> None:
        if self.action == ExecuteAction.RETURN:
            # For RETURN only max_responses is relevant
            if self.callback is not None:
                raise ValueError("RETURN action should not have a callback")
        elif self.action == ExecuteAction.MODIFY:
            if self.callback is None:
                raise ValueError("MODIFY action requires a callback")
            if self.max_modifications is None:
                raise ValueError("MODIFY action requires max_modifications")
        elif self.action == ExecuteAction.ALL:
            if self.callback is None:
                raise ValueError("ALL action requires a callback")
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
        callback: Callable[["Response"], Union["Response", Awaitable["Response"]]],
        max_modifications: Optional[int] = 1,
    ) -> "Execute":
        return cls(
            action=ExecuteAction.MODIFY,
            callback=callback,
            max_modifications=max_modifications,
        )

    @classmethod
    def ALL(
        cls,
        callback: Callable[["Response"], Union["Response", Awaitable["Response"]]],
        max_responses: Optional[int] = 1,
        max_modifications: Optional[int] = 1,
    ) -> "Execute":
        return cls(
            action=ExecuteAction.ALL,
            callback=callback,
            max_responses=max_responses,
            max_modifications=max_modifications,
        )
