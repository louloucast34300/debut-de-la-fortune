from dataclasses import dataclass
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domains.game import Game

# user_ids en attente — vit pour toute la durée du serveur
queue: list[str] = []

# parties actives en mémoire — game_id -> instance Game
active_games: dict[str, "Game"] = {}

@dataclass
class PendingMatch:
    players: list[dict]  # [{"id": "123", "accepted": None}, ...]

pending_matches: dict[str, PendingMatch] = {}


def try_create_match() -> tuple[str, PendingMatch] | None:
    """Appelé après chaque ajout dans la queue.
    Si 2 joueurs sont présents, crée un PendingMatch et les retire de la queue.
    Retourne (proposal_id, match) ou None si pas assez de joueurs.
    """
    if len(queue) < 2:
        return None

    players_ids = [queue.pop(0) for _ in range(2)]
    # proposal_id = C'est une protection contre les messages en retard / désynchronisés. 
    proposal_id = str(uuid.uuid4())
    match = PendingMatch(players=[{"id": pid, "accepted": None} for pid in players_ids])
    pending_matches[proposal_id] = match
    return proposal_id, match


def cancel_match(proposal_id: str, cancelled_by: str) -> list[str]:
    """Annule un match en attente.
    Retourne la liste des autres joueurs (à re-queue ou juste notifier selon le contexte d'appel).
    """
    match = pending_matches.pop(proposal_id, None)
    if not match:
        return []
    return [p["id"] for p in match.players if p["id"] != cancelled_by]