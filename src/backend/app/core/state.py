from dataclasses import dataclass
import uuid

# user_ids en attente — vit pour toute la durée du serveur
queue: list[str] = []

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
    """Appelé quand un joueur refuse ou se déconnecte pendant la modale.
    Re-queue les joueurs qui avaient accepté ou n'avaient pas encore répondu.
    Retourne la liste des user_ids re-quéués (pour envoyer les WS events).
    """
    match = pending_matches.pop(proposal_id, None)
    if not match:
        return []

    requeued = []
    for player in match.players:
        if player["id"] != cancelled_by and player["accepted"] is not False:
            queue.append(player["id"])
            requeued.append(player["id"])
    return requeued