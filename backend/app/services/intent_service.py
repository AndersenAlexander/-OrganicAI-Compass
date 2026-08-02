import re

UI_COMMANDS = {
    "open_home": ["open home", "go home", "deschide acasa", "pagina principala"],
    "open_diagnostic": ["open diagnostic", "start diagnostic", "deschide diagnosticul", "porneste diagnosticul"],
    "open_profile": ["open profile", "show profile", "open human potential map", "deschide harta potentialului", "arata harta potentialului"],
    "open_roadmap": ["show roadmap", "open roadmap", "show my roadmap", "arata mi roadmap ul", "deschide roadmap ul"],
    "open_fear_transformer": ["transform a fear", "open fear transformer", "transforma o frica"],
    "open_knowledge_base": ["open knowledge base", "deschide baza de cunostinte"],
    "open_report": ["generate report", "open report", "deschide raportul"],
    "open_learning_paths": ["open learning paths", "deschide traseele de invatare"],
    "open_coach": ["open coach", "open ai coach", "deschide coach ul"],
    "switch_dark_mode": ["switch to dark mode", "dark mode", "schimba in modul intunecat"],
    "switch_light_mode": ["switch to light mode", "light mode", "schimba in modul luminos"],
    "stop_speaking": ["stop speaking", "stop voice", "opreste vocea", "taci"],
    "repeat_answer": ["repeat answer", "repeat that", "repeta raspunsul"],
}
CONTEXT_COMMANDS = {"explain_selected_node": ["explain this node", "explain selected node"], "confirm_selected_node": ["confirm this interpretation", "confirm selected node"], "hide_selected_recommendation": ["hide this recommendation"], "open_selected_learning_path": ["open this learning path"], "read_seven_day_plan": ["read my seven day plan", "read seven day plan"], "read_thirty_day_plan": ["read my thirty day plan"], "read_six_month_plan": ["read my six month plan"], "regenerate_roadmap": ["regenerate roadmap"]}

def normalize(text: str) -> str:
    value = text.lower().strip().translate(str.maketrans("ăâîșț", "aais t".replace(" ", "")))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value)).strip()

async def classify_intent(text: str) -> dict:
    normalized = normalize(text)
    note_match = re.search(r"add a note(?: that)? (.+)", normalized)
    if note_match:
        return {"intent": "contextual_command", "confidence": 0.97, "command": {"name": "add_note_to_selected_node", "parameters": {"note": note_match.group(1)}}, "normalized_text": normalized, "requires_confirmation": True}
    for name, aliases in UI_COMMANDS.items():
        if any(alias in normalized for alias in aliases):
            return {"intent": "ui_command", "confidence": 0.99, "command": {"name": name, "parameters": {}}, "normalized_text": normalized, "requires_confirmation": False}
    for name, aliases in CONTEXT_COMMANDS.items():
        if any(alias in normalized for alias in aliases):
            return {"intent": "contextual_command", "confidence": 0.96, "command": {"name": name, "parameters": {}}, "normalized_text": normalized, "requires_confirmation": name in {"confirm_selected_node", "hide_selected_recommendation"}}
    if any(word in normalized for word in ("my profile", "my strengths", "my values", "archetype")): intent = "profile_question"
    elif any(word in normalized for word in ("roadmap", "seven day", "thirty day", "six month")): intent = "roadmap_question"
    elif any(word in normalized for word in ("fear", "afraid", "uncertain", "frica")): intent = "fear_transformation"
    elif any(word in normalized for word in ("privacy", "responsible ai", "robot", "future of work", "knowledge base")): intent = "knowledge_base_question"
    elif normalized: intent = "conversational_question"
    else: intent = "unknown"
    return {"intent": intent, "confidence": 0.82 if intent != "unknown" else 0.2, "command": None, "normalized_text": normalized, "requires_confirmation": False}
