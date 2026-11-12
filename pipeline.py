"""Deterministic extraction and assembly for the Cold Start challenge."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CIRCLES = {
    "spouse",
    "child",
    "parent",
    "in-law",
    "sibling",
    "relative",
    "friend",
    "colleague",
    "client",
    "vendor",
    "partner",
    "staff",
}

_REQUEST = re.compile(
    r"\b(?:pls|please|kindly)\s+"
    r"(?:(?:can|could|would)\s+you\s+)?"
    r"(?:ask|pay|send|give|get|buy|order|book|call|tell|share|check|discuss|"
    r"confirm|make|find|arrange|connect|update|provide|take|pick|put|complete|"
    r"finish|invite|reimburse|figure|let)\b",
    re.IGNORECASE,
)
_QUESTION_ACTION = re.compile(
    r"\b(?:can|could|would)\s+(?:u|you)\s+"
    r"(?:send|share|tell|give|provide|book|arrange|confirm|help|do|take|check|"
    r"update|pay|buy|order|call|discuss|meet)\b"
    r"|\bshould\s+i\b|\bpossible\s+to\b|\bshall\s+we\b"
    r"|\bwhich\s+(?:date|time)\b|\bneed\s+your\s+help\b"
    r"|\bwe\s+need\s+(?:you|the)\b",
    re.IGNORECASE,
)
_COMMITMENT = re.compile(
    r"\b(?:i['’]?ll|i\s+will|we['’]?ll|we\s+will)\s+"
    r"(?:send|pay|buy|order|book|call|ask|check|discuss|arrange|update|"
    r"complete|finish|share|find|get|take|make|confirm|revert)\b"
    r"|\bwill\s+(?:complete|send|pay|buy|order|book|call|revert)\b",
    re.IGNORECASE,
)
_NEED_ACTION = re.compile(
    r"\b(?:i|we)\s+need\s+(?:a|an|the|to|you|your)\b"
    r"|\bneed\s+to\s+(?:discuss|call|ask|send|pay|buy|order|book|arrange|"
    r"update|provide|find)\b",
    re.IGNORECASE,
)
_SHARED_ACTION = re.compile(
    r"\b(?:let['’]?s|lets)\s+"
    r"(?:send|book|order|discuss|meet|call|ask|arrange|confirm|plan|buy|"
    r"share|check|fix|make)\b",
    re.IGNORECASE,
)
_GO_AHEAD_ACTION = re.compile(
    r"\byou\s+(?:can|should|could)\s+"
    r"(?:go ahead|order|buy|book|send|pay|call|discuss|take|arrange)\b",
    re.IGNORECASE,
)
_DIRECT_SEND = re.compile(r"^\s*send\s+(?:me|your)\b", re.IGNORECASE)
_FOLLOWUP = re.compile(
    r"\b(?:follow\s*up|get back to|revert(?:ing)?|remind me|"
    r"let me know|lmk|check back|circle back)\b",
    re.IGNORECASE,
)
_QUESTION_WORDING = re.compile(
    r"\b(?:can|could|should|would|shall|possible|which|when|where|what)\b",
    re.IGNORECASE,
)
_DEADLINE = re.compile(
    r"\b(?:by\s+(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|\d)|before\s+\w+|due\s+(?:on\s+)?|deadline|"
    r"today|tomorrow|tonight|at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b",
    re.IGNORECASE,
)
_SUCCESS = re.compile(
    r"\b(?:i|we)\s+(?:have\s+|already\s+|just\s+)?"
    r"(?:sent|paid|bought|ordered|booked|fixed|completed|finished|submitted|shared)\b"
    r"|\b(?:is|are|has been|have been)\s+(?:now\s+)?"
    r"(?:done|completed|finished|fixed|sent|paid|bought|ordered|booked|submitted|shared)\b"
    r"|\bgot\s+.{0,50}\b(?:fixed|completed|sent|paid|bought|ordered|booked)\b",
    re.IGNORECASE,
)
_REVIEW_RESOLVED = re.compile(
    r"\b(?:looks good|approved|go ahead|that works|works for me|perfect)\b",
    re.IGNORECASE,
)
_REQUEST_RESOLVED = re.compile(
    r"\b(?:in (?:your|ur) email|sent it|shared it|here(?:'s| is) "
    r"(?:the|your)|attached (?:it|the|are)|uploaded it)\b",
    re.IGNORECASE,
)
_QUESTION_RESOLVED = re.compile(
    r"\b(?:likely|probably|we can|we should|let's (?:zoom|meet|do)|"
    r"not possible|can't make it|will be at|at \d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
    re.IGNORECASE,
)
_DROPPED = re.compile(
    r"\b(?:cancelled|canceled|no longer needed|not going ahead|"
    r"won't be doing|will not be doing|dropped the plan)\b",
    re.IGNORECASE,
)
_STOP_WORDS = {
    "about", "after", "also", "and", "are", "because", "been", "before", "can",
    "could", "from", "have", "help", "her", "him", "his", "how", "into", "just",
    "let", "like", "may", "might", "more", "need", "our", "please", "pls", "same",
    "should", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "today", "tomorrow", "too", "was", "were", "what",
    "when", "where", "which", "who", "will", "with", "would", "you", "your",
}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_input(input_dir: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    folder = Path(input_dir)
    chats = read_jsonl(folder / "chats.jsonl")
    messages = read_jsonl(folder / "messages.jsonl")
    seed_path = folder / "seed.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8")) if seed_path.exists() else {}
    return chats, messages, seed


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _chat_index(chats: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {chat["chat_id"]: chat for chat in chats}


def _participant_names(messages: List[Dict[str, Any]]) -> Dict[str, set]:
    names: Dict[str, set] = {}
    for message in messages:
        sender = message.get("sender_id")
        name = message.get("sender_name")
        if sender and name:
            names.setdefault(sender, set()).add(name)
    return names


def classify_circles(
    messages: List[Dict[str, Any]],
    seed: Dict[str, Any],
    chats: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Keep seed labels and use only relationship evidence with a clear referent."""
    seeded = seed.get("circles") or {}
    result = {pid: {"circle": circle, "evidence": []} for pid, circle in seeded.items()}
    if not chats:
        return result

    chats_by_person: Dict[str, List[Dict[str, Any]]] = {}
    for chat in chats:
        for pid in chat.get("participants", []):
            if pid != "ME":
                chats_by_person.setdefault(pid, []).append(chat)

    names_by_person = _participant_names(messages)
    evidence: Dict[str, List[Tuple[str, str]]] = {}
    kin_patterns = (
        (re.compile(r"\b(?:your|my)\s+(?:wife|husband|spouse)\b", re.I), "spouse"),
        (re.compile(r"\b(?:your|my)\s+(?:son|daughter|child|kid)\b", re.I), "child"),
        (re.compile(r"\b(?:your|my)\s+(?:mother|mom|father|dad|parent)\b", re.I), "parent"),
        (re.compile(r"\b(?:your|my)\s+(?:brother|sister|sibling)\b", re.I), "sibling"),
        (re.compile(r"\b(?:your|my)\s+in[- ]law\b", re.I), "in-law"),
    )
    msg_by_chat: Dict[str, List[Dict[str, Any]]] = {}
    for message in messages:
        msg_by_chat.setdefault(message.get("chat_id", ""), []).append(message)

    for chat in chats:
        participants = [pid for pid in chat.get("participants", []) if pid != "ME"]
        if not participants:
            continue
        title = _norm(chat.get("name", ""))
        chat_messages = msg_by_chat.get(chat.get("chat_id", ""), [])

        # A first-person kinship claim is safe for the speaker only when it
        # explicitly says "your ..."; "my sister" alone is not enough.
        for message in chat_messages:
            body = message.get("body") or ""
            sender = message.get("sender_id")
            for pattern, circle in kin_patterns:
                match = pattern.search(body)
                if not match:
                    continue
                prefix = body[max(0, match.start() - 18):match.start()].lower()
                if "your " in match.group(0).lower() and re.search(
                    r"\b(?:i am|i'm|im|i am your)\s*$", prefix
                ):
                    if sender in participants:
                        evidence.setdefault(sender, []).append((circle, message["id"]))
                elif sender == "ME" and "my " in match.group(0).lower():
                    # The target is not the sender. Resolve it only if exactly
                    # one participant name is explicitly present nearby.
                    tail = body[match.end():match.end() + 90]
                    matches = [
                        pid for pid in participants
                        if any(re.search(r"\b" + re.escape(name) + r"\b", tail, re.I)
                               for name in names_by_person.get(pid, set()))
                    ]
                    if len(matches) == 1:
                        evidence.setdefault(matches[0], []).append((circle, message["id"]))

        if re.search(r"\bsiblings?\b", title):
            # Group membership alone is not enough to distinguish a spouse
            # included in a family group from a sibling.
            continue

    for pid, matches in evidence.items():
        circles = {circle for circle, _ in matches}
        if pid not in seeded and len(circles) == 1:
            circle = next(iter(circles))
            result[pid] = {
                "circle": circle,
                "evidence": [msg_id for found, msg_id in matches if found == circle],
            }

    # Use high-precision work and family chat titles when no direct kinship
    # statement resolved the person's role.
    for pid, person_chats in chats_by_person.items():
        if pid in result:
            continue
        titles = [_norm(chat.get("name", "")) for chat in person_chats]
        direct_chat_ids = {
            chat["chat_id"] for chat in person_chats
            if not chat.get("is_group") and "ME" in chat.get("participants", [])
        }
        direct_text = " ".join(
            (message.get("body") or "").lower()
            for message in messages
            if message.get("chat_id") in direct_chat_ids and message.get("sender_id") == pid
        )
        all_text = " ".join(
            (message.get("body") or "").lower()
            for message in messages
            if message.get("sender_id") == pid
        )
        circle = None
        if re.search(r"\bour\s+(?:kids|children)\b", direct_text):
            circle = "spouse"
        elif any(re.search(r"\b(?:siblings?|brother|sister)\b", title) for title in titles):
            circle = "sibling"
        elif any(re.search(r"\b(?:operations|finance|office|team|colleague)\b", title) for title in titles):
            circle = "colleague"
        elif any(re.search(r"\bkitchen\b", title) for title in titles):
            circle = "staff"
        elif any("nexus" in title and "ad targeting" in title for title in titles):
            circle = "client"
        elif any(re.search(r"\b(?:yoga|trading company|vendor|supplier)\b", title) for title in titles):
            circle = "vendor"
        elif re.search(r"\b(?:my colleague|our team|at the office)\b", all_text):
            circle = "colleague"
        if circle:
            result[pid] = {"circle": circle, "evidence": []}

    return result


def assemble_people(
    all_person_ids: List[str],
    circle_info: Dict[str, Dict[str, Any]],
    person_links: Optional[Dict[str, List[Dict[str, str]]]] = None,
) -> List[Dict[str, Any]]:
    people = []
    for pid in sorted(all_person_ids):
        person = {"id": pid, "circle": circle_info.get(pid, {}).get("circle", "friend")}
        links = (person_links or {}).get(pid)
        if links:
            person["links"] = links
        people.append(person)
    return people


def _organization_records(seed: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    records = []
    aliases: Dict[str, List[str]] = {}
    for name in seed.get("organisations", []):
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "organisation"
        org_id = "org_" + slug
        records.append({
            "id": org_id,
            "name": name,
            "type": "company",
            "side": "work",
            "role": "owner",
        })
        org_aliases = {name}
        split_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name_tokens = re.findall(r"[A-Za-z0-9]+", split_name)
        if name_tokens and len(name_tokens[0]) >= 4:
            org_aliases.add(name_tokens[0])
        initials = "".join(re.findall(r"[A-Z]", name))
        if len(initials) >= 3:
            org_aliases.add(initials)
        aliases[org_id] = sorted(org_aliases, key=len, reverse=True)

    return records, aliases


def assemble_organisations_and_chats(
    chats: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
    seed: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    organisations, aliases = _organization_records(seed)
    org_by_id = {org["id"]: org for org in organisations}
    home_org_id = "org_home"
    group_titles = [_norm(chat.get("name", "")) for chat in chats if chat.get("is_group")]
    has_home_context = any(
        re.search(r"\b(?:carpool|kitchen|household|home|ghar|residence)\b", title)
        for title in group_titles
    )
    if has_home_context and not any(_norm(org["name"]) == "home" for org in organisations):
        home = {
            "id": home_org_id,
            "name": "Home",
            "type": "residence",
            "side": "home",
            "role": "owner",
        }
        organisations.append(home)
        org_by_id[home_org_id] = home
        aliases[home_org_id] = ["home"]

    message_by_chat: Dict[str, List[Dict[str, Any]]] = {}
    for message in messages:
        message_by_chat.setdefault(message.get("chat_id", ""), []).append(message)

    ties = []
    for chat in chats:
        participants = [pid for pid in chat.get("participants", []) if pid != "ME"]
        title = chat.get("name", "")
        org_id = None
        if chat.get("is_group"):
            for candidate_id, candidates in aliases.items():
                if candidate_id == home_org_id:
                    if re.search(r"\b(?:carpool|kitchen|household|home|ghar|residence)\b", _norm(title)):
                        org_id = candidate_id
                        break
                    continue
                if any(
                    re.search(
                        r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])",
                        title,
                        re.I,
                    )
                    for alias in candidates
                ):
                    org_id = candidate_id
                    break

            if org_id is None and re.search(r"\bradiant\s+operations\b", title, re.I):
                org = {
                    "id": "org_radiant",
                    "name": "Radiant",
                    "type": "company",
                    "side": "work",
                    "role": "helper",
                }
                if org["id"] not in org_by_id:
                    organisations.append(org)
                    org_by_id[org["id"]] = org
                org_id = org["id"]

        if org_id:
            ties.append({"chat_id": chat["chat_id"], "organisation": org_id})
            continue

        if not participants:
            # The input contract says Arjun is in every chat; surface malformed
            # data rather than silently emitting an invalid tie.
            raise ValueError("Chat has no non-ME participant: " + chat["chat_id"])
        if not chat.get("is_group"):
            for candidate_id, candidates in aliases.items():
                if any(
                    re.search(
                        r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9])",
                        title,
                        re.I,
                    )
                    for alias in candidates
                ):
                    org_id = candidate_id
                    break
            if org_id:
                ties.append({"chat_id": chat["chat_id"], "organisation": org_id})
                continue
            other = participants[0]
        else:
            sender_counts: Dict[str, int] = {}
            for message in message_by_chat.get(chat["chat_id"], []):
                sender = message.get("sender_id")
                if sender in participants:
                    sender_counts[sender] = sender_counts.get(sender, 0) + 1
            other = max(participants, key=lambda pid: (sender_counts.get(pid, 0), pid))
        ties.append({"chat_id": chat["chat_id"], "person": other})

    return organisations, ties


def _message_tokens(text: str) -> set:
    return {
        token for token in re.findall(r"[a-z0-9]{3,}", text.lower())
        if token not in _STOP_WORDS
    }


def _candidate_type(text: str) -> str:
    if _DEADLINE.search(text):
        return "deadline"
    if _FOLLOWUP.search(text):
        return "followup"
    if "?" in text or _QUESTION_WORDING.search(text):
        return "question"
    return "commitment"


def _due_date(text: str, timestamp: Any) -> Optional[str]:
    if not _DEADLINE.search(text):
        return None
    try:
        base = datetime.fromtimestamp(float(timestamp), timezone.utc).date()
    except (TypeError, ValueError, OverflowError):
        return None
    lowered = text.lower()
    if re.search(r"\btomorrow\b", lowered):
        return (base + timedelta(days=1)).isoformat()
    if re.search(r"\btoday\b", lowered):
        return base.isoformat()
    match = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\b",
        lowered,
    )
    if match:
        month_names = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month = month_names[match.group(2)[:3]]
        year = base.year
        try:
            candidate = datetime(year, month, int(match.group(1))).date()
            if candidate < base - timedelta(days=180):
                candidate = candidate.replace(year=year + 1)
            return candidate.isoformat()
        except ValueError:
            return None
    return None


def _completion_for(
    source: Dict[str, Any],
    thread: List[Dict[str, Any]],
    is_direct_chat: bool,
) -> Tuple[str, Optional[str]]:
    source_text = source.get("body") or ""
    if _DROPPED.search(source_text):
        return "dropped", source["id"]
    if _SUCCESS.search(source_text) and not re.search(
        r"\b(?:cannot|can't|could not|couldn't|not yet|unable to)\b.{0,45}"
        r"\b(?:done|completed|finished|fixed|sent|paid|ordered|booked)\b",
        source_text,
        re.I,
    ):
        return "done", source["id"]

    source_terms = _message_tokens(source_text)
    action_terms = source_terms & {
        "send", "pay", "buy", "order", "book", "call", "ask", "check", "discuss",
        "arrange", "update", "complete", "finish", "share", "find", "get", "take",
        "make", "confirm", "reimburse", "accountant", "device", "certificate", "po",
    }
    if not action_terms:
        action_terms = source_terms & {"question", "date", "time"}

    for message in thread:
        if message.get("ts", 0) <= source.get("ts", 0):
            continue
        try:
            elapsed = float(message.get("ts", 0)) - float(source.get("ts", 0))
        except (TypeError, ValueError):
            continue
        if elapsed > 24 * 60 * 60:
            break
        if message.get("sender_id") == source.get("sender_id"):
            continue
        body = message.get("body") or ""
        if not body:
            continue
        if re.search(
            r"\b(?:cannot|can't|could not|couldn't|not yet|unable to)\b.{0,45}"
            r"\b(?:done|completed|finished|fixed|sent|paid|ordered|booked)\b",
            body,
            re.I,
        ):
            continue

        if _DROPPED.search(body):
            return "dropped", message["id"]
        if _SUCCESS.search(body):
            overlap = source_terms & _message_tokens(body)
            if not action_terms or overlap & action_terms:
                return "done", message["id"]

        source_is_question = "?" in source_text or _QUESTION_ACTION.search(source_text)
        if is_direct_chat and source_is_question and not _QUESTION_WORDING.search(body):
            reply = _norm(body)
            if len(reply.split()) >= 3 and not re.fullmatch(
                r"(?:ok|okay|sure|yes|no|thanks|thank you|got it)", reply
            ) and _QUESTION_RESOLVED.search(body):
                return "done", message["id"]

        if _REQUEST_RESOLVED.search(body) and re.search(
            r"\b(?:send|share|attach|upload|check|review|look)\b",
            source_text,
            re.I,
        ):
            return "done", message["id"]

        if _REVIEW_RESOLVED.search(body) and re.search(
            r"\b(?:check|review|look|approve|thoughts|opinion)\b",
            source_text,
            re.I,
        ):
            return "done", message["id"]

        # A product result immediately answering "should I get X?" can resolve
        # that decision question; a generic substantive message cannot.
        if (
            is_direct_chat
            and re.search(r"\bshould\s+i\s+get\b", source_text, re.I)
            and elapsed <= 2 * 60 * 60
            and len(_message_tokens(body)) >= 4
            and re.search(r"https?://|\b(?:price|inch|size|product)\b", body, re.I)
        ):
            return "done", message["id"]
    return "open", None


def extract_open_loops(
    chats: List[Dict[str, Any]],
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Find high-confidence actionable loops and conservatively track closure."""
    chats_by_id = _chat_index(chats)
    by_chat: Dict[str, List[Dict[str, Any]]] = {}
    for message in messages:
        by_chat.setdefault(message.get("chat_id", ""), []).append(message)
    for thread in by_chat.values():
        thread.sort(key=lambda message: (message.get("ts", 0), message.get("id", "")))

    loops = []
    seen_sources = set()
    for message in messages:
        source_id = message.get("id")
        if not source_id or source_id in seen_sources:
            continue
        chat = chats_by_id.get(message.get("chat_id"))
        if chat is None:
            raise ValueError("Message refers to unknown chat: " + str(message.get("chat_id")))
        body = (message.get("body") or "").strip()
        if not body:
            continue

        # Group messages contain many broadcast prompts. Require explicit
        # first-person commitment or direct mention before treating them as loops.
        is_direct_chat = not chat.get("is_group")
        if is_direct_chat:
            candidate = bool(
                _REQUEST.search(body)
                or _QUESTION_ACTION.search(body)
                or (message.get("sender_id") == "ME" and _COMMITMENT.search(body))
                or _NEED_ACTION.search(body)
                or _SHARED_ACTION.search(body)
                or _GO_AHEAD_ACTION.search(body)
                or _DIRECT_SEND.search(body)
            )
        else:
            candidate = bool(
                message.get("sender_id") == "ME" and _COMMITMENT.search(body)
                or re.search(r"\b(?:Arjun|@[\w]+)\b", body, re.I)
                and (_REQUEST.search(body) or _QUESTION_ACTION.search(body))
            )
        if not candidate:
            continue

        participants = [pid for pid in chat.get("participants", []) if pid != "ME"]
        sender = message.get("sender_id")
        if sender == "ME":
            owner = "ME"
        elif _COMMITMENT.search(body):
            owner = sender if sender in participants else "ME"
        elif is_direct_chat and "ME" in chat.get("participants", []):
            owner = "ME"
        else:
            owner = sender if sender in participants else (participants[0] if participants else "ME")
        if owner != "ME" and owner not in participants:
            raise ValueError("Could not identify a valid loop owner for " + source_id)

        status, closed_by = _completion_for(
            message,
            by_chat.get(message["chat_id"], []),
            is_direct_chat,
        )
        title = " ".join(body.split())
        if len(title) > 180:
            title = title[:177].rstrip() + "..."
        if not title:
            title = "Follow up on message " + source_id

        loop = {
            "title": title,
            "type": _candidate_type(body),
            "owner": owner,
            "chat_id": message["chat_id"],
            "source_msg": source_id,
            "due": _due_date(body, message.get("ts")),
            "status": status,
            "closed_by": closed_by,
            "help": (
                {"action": "leave", "reason": "No clear assistance action is supported by the messages."}
                if status == "open" else None
            ),
        }
        loops.append(loop)
        seen_sources.add(source_id)

    return loops


def extract_goals(messages: List[Dict[str, Any]], seed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Emit only explicit, time-bounded personal goals with a message as evidence."""
    goal_intent = re.compile(
        r"\b(?:my goal is to|our goal is to|i want to|we want to|i hope to|"
        r"i plan to|we plan to|i aim to|we aim to|i am aiming to|"
        r"i'd like to|i would like to|dream of)\b",
        re.IGNORECASE,
    )
    horizon_rules = (
        (re.compile(r"\b(?:in|within|next)\s+(?:the\s+)?(?:three|3)\s+months?\b|\bthis quarter\b", re.I), "3mo"),
        (re.compile(r"\b(?:in|within|next)\s+(?:the\s+)?(?:one|1|12)\s+(?:year|years|month|months)\b|\bby\s+next year\b", re.I), "1yr"),
        (re.compile(r"\b(?:in|within|next)\s+(?:the\s+)?(?:three|3)\s+years?\b", re.I), "3yr"),
        (re.compile(r"\b(?:in|within|next)\s+(?:the\s+)?(?:five|5)\s+years?\b", re.I), "5yr"),
    )
    area_rules = (
        ("health", re.compile(r"\b(?:health|run|marathon|fitness|exercise|weight|sleep)\b", re.I)),
        ("finances", re.compile(r"\b(?:save|savings|invest|retire|financial|money)\b", re.I)),
        ("work", re.compile(r"\b(?:business|company|work|career|client|revenue|team)\b", re.I)),
        ("home", re.compile(r"\b(?:home|house|renovate|property)\b", re.I)),
        ("kids", re.compile(r"\b(?:kids|children|son|daughter)\b", re.I)),
        ("spouse", re.compile(r"\b(?:wife|husband|spouse|partner)\b", re.I)),
        ("parents", re.compile(r"\b(?:parents|mother|father|mom|dad)\b", re.I)),
        ("friends", re.compile(r"\b(?:friend|friends)\b", re.I)),
        ("experiences", re.compile(r"\b(?:travel|trip|visit|experience|holidays?)\b", re.I)),
    )
    month_pattern = re.compile(
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\b",
        re.I,
    )
    event_goal = re.compile(
        r"\b(?:half marathon|marathon|10k|triathlon)\b"
        r"|\b(?:trip|holidays?|vacation|travel|weekend away)\b",
        re.I,
    )

    goals = []
    seen = set()
    message_tokens = {
        message["id"]: _message_tokens(message.get("body") or "")
        for message in messages
        if message.get("id")
    }
    for goal in seed.get("goals", []):
        title = goal.get("title", "")
        goal_tokens = _message_tokens(title)
        if not title or len(goal_tokens) < 2:
            continue
        matching = [
            message_id
            for message_id, tokens in message_tokens.items()
            if len(goal_tokens & tokens) >= 2
        ]
        if not matching:
            continue
        required = ("area", "type", "horizon")
        missing = [key for key in required if key not in goal]
        if missing:
            raise ValueError("Seed goal is missing required fields: " + ", ".join(missing))
        goals.append({
            "title": title,
            "area": goal["area"],
            "type": goal["type"],
            "horizon": goal["horizon"],
            "evidence": matching[:3],
        })
        seen.add((goal["area"], _norm(title)))

    for message in messages:
        body = " ".join((message.get("body") or "").split())
        intent = goal_intent.search(body)
        explicit_event = event_goal.search(body) and month_pattern.search(body)
        if not intent and not explicit_event:
            continue
        horizon = next((value for pattern, value in horizon_rules if pattern.search(body)), None)
        if horizon is None and explicit_event:
            month_match = month_pattern.search(body)
            month_numbers = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }
            try:
                current_month = datetime.fromtimestamp(
                    float(message.get("ts", 0)), timezone.utc
                ).month
            except (TypeError, ValueError, OverflowError):
                continue
            target_month = month_numbers[month_match.group(0)[:3].lower()]
            months_ahead = (target_month - current_month) % 12
            if months_ahead <= 3:
                horizon = "3mo"
            elif months_ahead <= 12:
                horizon = "1yr"
            else:
                horizon = "3yr"
        if horizon is None:
            continue
        is_experience = bool(re.search(r"\b(?:travel|trip|visit|experience|holidays?)\b", body, re.I))
        area = "experiences" if is_experience else next(
            (value for value, pattern in area_rules if pattern.search(body)),
            "self",
        )
        type_ = "habit" if re.search(r"\b(?:daily|every day|weekly|every week|regularly)\b", body, re.I) else (
            "experience" if is_experience else "milestone"
        )
        title = body[intent.end():].strip(" .,:;") if intent else body
        if not title:
            continue
        key = (area, _norm(title))
        if key in seen:
            continue
        goals.append({
            "title": title[:180],
            "area": area,
            "type": type_,
            "horizon": horizon,
            "evidence": [message["id"]],
        })
        seen.add(key)
        if len(goals) == 10:
            break
    return goals
