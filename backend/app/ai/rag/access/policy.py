from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeAccessContext:
    user_id: int
    team_id: int | None


class KnowledgeAccessPolicy:

    def can_access(
        self,
        *,
        owner_team_id: int | None,
        context: KnowledgeAccessContext,
    ) -> bool:
        # Shared knowledge.
        if owner_team_id is None:
            return True

        # Team-owned knowledge.
        return (
            context.team_id is not None
            and context.team_id == owner_team_id
        )
