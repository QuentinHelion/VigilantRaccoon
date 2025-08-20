# use_cases/filter_exceptions.py
from ipaddress import ip_address, ip_network

def _ip_in_networks(ip_str: str, nets: list[str]) -> bool:
    if not ip_str:
        return False
    try:
        ip = ip_address(ip_str)
    except ValueError:
        return False
    for n in nets or []:
        try:
            if ip in ip_network(n, strict=False):
                return True
        except ValueError:
            # entrée non valide : on ignore
            continue
    return False

def _match_pair(user: str | None, ip_str: str | None, pairs: list[dict]) -> bool:
    if not pairs:
        return False
    u = (user or "").lower()
    for rule in pairs:
        ru = (rule.get("user") or "").lower()
        ra = rule.get("address")
        ok_user = (not ru) or (u == ru)
        ok_addr = (not ra) or _ip_in_networks(ip_str, [ra])
        if ok_user and ok_addr:
            return True
    return False

def should_filter_ssh_alert(user: str | None, ip_str: str | None, exceptions_cfg: dict | None) -> tuple[bool, str | None]:
    """
    Retourne (filtered, downgrade_to)
    - filtered = True si l’alerte doit être supprimée
    - downgrade_to = "info"/... si l’alerte doit être déclassée (sinon None)
    """
    if not exceptions_cfg:
        return (False, None)

    ssh_cfg = (exceptions_cfg or {}).get("ssh") or {}
    action = (ssh_cfg.get("action") or "suppress").lower()
    downgrade_to = (ssh_cfg.get("downgrade_to") or "info").lower()

    ignore_users = [(u or "").lower() for u in (ssh_cfg.get("ignore_users") or [])]
    ignore_addrs = ssh_cfg.get("ignore_addresses") or []
    ignore_pairs = ssh_cfg.get("ignore_rules") or []

    u = (user or "").lower()

    # Match simple par user
    if u and u in ignore_users:
        return (True, None) if action == "suppress" else (False, downgrade_to)

    # Match simple par IP/CIDR
    if _ip_in_networks(ip_str, ignore_addrs):
        return (True, None) if action == "suppress" else (False, downgrade_to)

    # Match combiné (user + address, champs optionnels)
    if _match_pair(user, ip_str, ignore_pairs):
        return (True, None) if action == "suppress" else (False, downgrade_to)

    return (False, None)
